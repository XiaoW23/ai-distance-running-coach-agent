import os
import json
import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sqlite3
import uuid
import os
import aiosqlite
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_core.runnables import RunnableConfig
from pydantic import SecretStr

from backend.agent import get_agent

app = FastAPI(title="Running Training Agent API")

# Initialize sessions table
db_conn = sqlite3.connect("running_memory.db", check_same_thread=False)
db_conn.execute("CREATE TABLE IF NOT EXISTS user_sessions (thread_id TEXT PRIMARY KEY, title TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
db_conn.commit()

# Define request model
class ChatRequest(BaseModel):
    message: str
    thread_id: str

class SessionCreate(BaseModel):
    title: str

class SessionUpdate(BaseModel):
    title: str

class TruncateRequest(BaseModel):
    from_message_id: str

class DeleteMessagesRequest(BaseModel):
    message_ids: list[str]

async def generate_title_async(thread_id: str, first_message: str):
    try:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("未找到 DEEPSEEK_API_KEY，请在 .env 文件中设置。")
        base_url = "https://api.deepseek.com/v1"
        llm = ChatOpenAI(model="deepseek-chat", api_key=SecretStr(api_key), base_url=base_url, temperature=0.3)
        prompt = [
            SystemMessage(content="请根据用户的首次提问，概括出一个短于10个字的任务标题。直接输出标题内容，不要带任何标点、引号或多余解释。"),
            HumanMessage(content=first_message)
        ]
        response = await llm.ainvoke(prompt)
        title = str(response.content).strip().strip('"').strip("'")
        if len(title) > 15:
            title = title[:15]
            
        async with aiosqlite.connect("running_memory.db") as db:
            await db.execute("UPDATE user_sessions SET title = ? WHERE thread_id = ?", (title, thread_id))
            await db.commit()
    except Exception as e:
        print(f"Auto-title error: {e}")

@app.get("/sessions")
def get_sessions():
    cursor = db_conn.cursor()
    cursor.execute("SELECT thread_id, title, updated_at FROM user_sessions ORDER BY updated_at DESC")
    sessions = [{"thread_id": row[0], "title": row[1], "updated_at": row[2]} for row in cursor.fetchall()]
    return {"sessions": sessions}

@app.post("/sessions")
def create_session(data: SessionCreate):
    thread_id = str(uuid.uuid4())
    cursor = db_conn.cursor()
    cursor.execute("INSERT INTO user_sessions (thread_id, title) VALUES (?, ?)", (thread_id, data.title))
    db_conn.commit()
    return {"thread_id": thread_id, "title": data.title}

@app.get("/history/{thread_id}")
async def get_history(thread_id: str):
    messages = []
    async with AsyncSqliteSaver.from_conn_string("running_memory.db") as checkpointer:
        agent = get_agent(checkpointer)
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        state = await agent.aget_state(config)
        if hasattr(state, 'values') and 'messages' in state.values:
            for msg in state.values['messages']:
                if msg.type in ["human", "ai"] and msg.content:
                    role = "user" if msg.type == "human" else "ai"
                    messages.append({"id": msg.id, "role": role, "content": msg.content})
    return {"messages": messages}

@app.post("/history/{thread_id}/truncate")
async def truncate_history(thread_id: str, request: TruncateRequest):
    async with AsyncSqliteSaver.from_conn_string("running_memory.db") as checkpointer:
        agent = get_agent(checkpointer)
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        state = await agent.aget_state(config)
        
        if not hasattr(state, 'values') or 'messages' not in state.values:
            return {"status": "ok"}
            
        messages = state.values['messages']
        idx = -1
        for i, msg in enumerate(messages):
            if getattr(msg, 'id', None) == request.from_message_id:
                idx = i
                break
                
        if idx == -1:
            return {"status": "ok", "deleted": 0}
            
        messages_to_delete = messages[idx:]
        if messages_to_delete:
            remove_messages = [RemoveMessage(id=msg.id) for msg in messages_to_delete if getattr(msg, 'id', None)]
            await agent.aupdate_state(config, {"messages": remove_messages})
            
        return {"status": "ok", "deleted": len(messages_to_delete)}

@app.delete("/history/{thread_id}/messages")
async def delete_messages(thread_id: str, request: DeleteMessagesRequest):
    async with AsyncSqliteSaver.from_conn_string("running_memory.db") as checkpointer:
        agent = get_agent(checkpointer)
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        
        remove_messages = [RemoveMessage(id=mid) for mid in request.message_ids if mid]
        if remove_messages:
            await agent.aupdate_state(config, {"messages": remove_messages})
        
        return {"status": "ok"}

@app.delete("/sessions/{thread_id}")
def delete_session(thread_id: str):
    cursor = db_conn.cursor()
    cursor.execute("DELETE FROM user_sessions WHERE thread_id = ?", (thread_id,))
    db_conn.commit()
    return {"status": "ok"}

@app.put("/sessions/{thread_id}")
def update_session(thread_id: str, data: SessionUpdate):
    cursor = db_conn.cursor()
    cursor.execute("UPDATE user_sessions SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE thread_id = ?", (data.title, thread_id))
    db_conn.commit()
    return {"status": "ok"}

# Endpoint for chatting with the agent via SSE (Server-Sent Events)
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # Retrieve current title to check if it's new
    cursor = db_conn.cursor()
    cursor.execute("SELECT title FROM user_sessions WHERE thread_id = ?", (request.thread_id,))
    row = cursor.fetchone()
    current_title = row[0] if row else ""
    
    # Update timestamp
    cursor.execute("UPDATE user_sessions SET updated_at = CURRENT_TIMESTAMP WHERE thread_id = ?", (request.thread_id,))
    db_conn.commit()
    
    async def event_stream():
        if current_title and current_title.startswith("新对话"):
            import asyncio
            asyncio.create_task(generate_title_async(request.thread_id, request.message))
            
        async with AsyncSqliteSaver.from_conn_string("running_memory.db") as checkpointer:
            agent = get_agent(checkpointer)
            config: RunnableConfig = {"configurable": {"thread_id": request.thread_id}}
            inputs: dict = {"messages": [("user", request.message)]}
            
            try:
                # We use astream_events with version="v2" as it's standard for LangChain 0.2+
                async for event in agent.astream_events(inputs, config=config, version="v2"):  # type: ignore[arg-type]
                    kind = event["event"]
                    # Stream new tokens from the model
                    if kind == "on_chat_model_stream":
                        content = event["data"]["chunk"].content
                        if content:
                            # Format as SSE
                            yield f"data: {json.dumps({'type': 'token', 'content': content}, ensure_ascii=False)}\n\n"
                    
                    # Stream tool start events
                    elif kind == "on_tool_start":
                        tool_name = event["name"]
                        yield f"data: {json.dumps({'type': 'tool_start', 'content': f'正在调用工具: {tool_name}...'}, ensure_ascii=False)}\n\n"
                    
                    # Stream tool end events
                    elif kind == "on_tool_end":
                        tool_name = event["name"]
                        yield f"data: {json.dumps({'type': 'tool_end', 'content': f'工具 {tool_name} 调用完成。'}, ensure_ascii=False)}\n\n"
                
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

# Mount frontend static files
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
