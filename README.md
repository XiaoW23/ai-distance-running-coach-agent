# AI 中长跑教练智能体 (LangGraph + RAG)

这是一个基于 `LangGraph` 和大语言模型的智能中长跑训练辅助系统。该系统能够通过知识库查阅《丹尼尔斯经典跑步训练法》，并能够解析用户上传的 Coros 跑表数据（CSV格式）来计算生理负荷。

系统采用“前置白盒路由”架构，极大程度减少了 Token 消耗并避免了模型幻觉。

## 🎯 系统架构图

本项目抛弃了传统的 ReAct 盲猜调用机制，通过纯代码的条件边 (`Conditional Edges`) 实现了精准的流程控制。

```mermaid
graph TD
    START((START)) --> router_node{路由决策<br/>纯代码判断}
    
    router_node -->|包含 CSV 跑表数据| data_node[data_node<br/>解析 CSV 并计算 TRIMP 负荷]
    router_node -->|包含理论/恢复等关键词| rag_node[rag_node<br/>查询本地 ChromaDB 知识库]
    router_node -->|普通闲聊| llm_node[llm_node<br/>大语言模型综合总结]
    
    data_node -->|提取的生理指标注入 Context| llm_node
    rag_node -->|检索的训练理论注入 Context| llm_node
    
    llm_node --> END((END))

## 🚀 极速体验指南

本项目支持**原生环境直接启动**或通过**Docker 容器化**一键部署。在运行项目前，请确保在根目录创建 `.env` 文件，并填入：

```env
DEEPSEEK_API_KEY="您的真实_API_KEY"
DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"
```

### 方式一：Docker 容器化运行（出厂满血版 - 推荐）

为了解决环境冲突，本项目已配置为“构建即向量化”模式。在构建镜像时，系统会自动下载 HuggingFace 的本地 Embedding 模型，并将 `data/` 目录下的所有语料持久化生成内置的 `chroma_db`。

1. **构建镜像**（需要耗费少许时间预下载本地权重文件）：
   ```bash
   docker build -t run_agent .
   ```
2. **启动容器**：
   ```bash
   docker run -p 8000:8000 run_agent
   ```
3. 在浏览器打开：`http://localhost:8000`

### 方式二：本地原生运行（开发测试用）

1. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```
2. **（可选）手动重建知识库**（当您在 `data/` 文件夹下新增了 txt 语料后必须执行）：
   ```bash
   python rebuild_db.py
   ```
3. **拉起服务**：
   直接双击 `start.bat`，或在命令行运行：
   ```bash
   uvicorn backend.main:app --reload
   ```
4. 在浏览器打开：`http://localhost:8000`
