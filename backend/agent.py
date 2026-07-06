import os
import re
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from backend.rag import retrieve_knowledge

load_dotenv()

# 1. 定义 State
def add_context(left: str, right: str):
    if not right:  # 收到空字符串时，清空 context
        return ""
    if not left:
        return right
    return left + "\n\n" + right

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    context: Annotated[str, add_context]


def _get_last_text(state: AgentState) -> str:
    """安全获取最后一条消息的文本内容"""
    content = state["messages"][-1].content
    if isinstance(content, str):
        return content
    for part in content:
        if isinstance(part, dict) and part.get("type") == "text":
            return part["text"]
    return ""


# 1.5. 定义数学前置节点 (拦截并剥夺大模型的计算权)
def math_node(state: AgentState):
    last_message = _get_last_text(state)
    assessment = ""
    
    # 提取比赛成绩 (e.g. 800m跑了2分15秒)
    race_match = re.search(r'(\d+)\s*(?:米|m).*?(?:跑了|成绩).*?(\d+)\s*[:分]\s*(\d+)', last_message, re.IGNORECASE)
    if race_match:
        from backend.pace_utils import RunningPaceCalculator
        race_dist = int(race_match.group(1))
        race_time_seconds = int(race_match.group(2)) * 60 + int(race_match.group(3))
        paces = RunningPaceCalculator.get_daniels_training_paces(race_dist, race_time_seconds)
        if "error" not in paces:
            assessment += f"【系统前置计算：VDOT与配速推演】\n"
            assessment += f"解析到历史成绩：{race_dist}m, 耗时 {race_match.group(2)}:{race_match.group(3)}。\n"
            assessment += f"推算跑力值 -> Speed_VDOT: {paces['Speed_VDOT']}, Endurance_VDOT: {paces['Endurance_VDOT']}\n"
            assessment += f"以下为系统强制分配的标准配速，大模型必须严格引用，严禁篡改或自行计算：\n"
            assessment += f"E跑配速: {paces['E_pace']}\n"
            assessment += f"M跑配速: {paces['M_pace']}\n"
            assessment += f"T跑(乳酸阈值)配速: {paces['T_pace']}\n"
            assessment += f"I跑配速: {paces['I_pace']}\n"
            assessment += f"R跑(绝对速度)配速: {paces['R_pace']}\n\n"

    # 提取步频和步幅，提前算好配速
    cadence_match = re.search(r'(\d+)\s*(?:spm|步频)', last_message, re.IGNORECASE)
    stride_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:m|米\b|步幅)', last_message, re.IGNORECASE)
    if cadence_match and stride_match:
        cadence = float(cadence_match.group(1))
        stride = float(stride_match.group(1))
        actual_cadence = cadence * 2 if cadence < 120 else cadence
        speed_m_per_min = actual_cadence * stride
        if speed_m_per_min > 0:
            pace_decimal = 1000 / speed_m_per_min
            pace_min = int(pace_decimal)
            pace_sec = int((pace_decimal - pace_min) * 60)
            assessment += f"【系统前置计算：步频步幅物理验算】\n"
            assessment += f"用户提及了 步频 {cadence} 和 步幅 {stride}m。\n"
            assessment += f"系统计算真实配速 = 1000 / ({actual_cadence} × {stride}) = {pace_min}:{pace_sec:02d}/km。\n"
            assessment += f"在给出建议时，你必须严格引用该系统提前计算好的物理配速结果，比对该结果是否超出用户当前 VDOT 水平。如果超出，请在回答中指出建议不合理并驳回，严禁自行重新计算！\n"
            
    return {"context": assessment} if assessment else {}

# 2. 定义 RAG 节点
def rag_node(state: AgentState):
    last_message = _get_last_text(state)
    try:
        docs = retrieve_knowledge(last_message)
        context = f"【《丹尼尔斯经典跑步训练法》知识库检索结果】\n{docs}"
    except Exception as e:
        context = f"【知识库检索失败】\n{str(e)}"
    
    return {"context": context}

# 3. 定义数据解析节点 (替代原先大模型盲猜调用的 Tool)
def data_node(state: AgentState):
    last_message = _get_last_text(state)
    
    # 纯 Python 的正则表达式解析
    # 尝试提取距离(km)、时间(min)和心率(bpm)
    distance_match = re.search(r'(距离|Distance)[\s:=]*([\d\.]+)', last_message, re.IGNORECASE)
    duration_match = re.search(r'(时间|Time|时长)[\s:=]*([\d\.]+)', last_message, re.IGNORECASE)
    hr_match = re.search(r'(心率|HR|Heart Rate)[\s:=]*(\d+)', last_message, re.IGNORECASE)
    
    if distance_match and hr_match:
        dist = float(distance_match.group(2))
        hr = int(hr_match.group(2))
        dur = float(duration_match.group(2)) if duration_match else 30.0 # 默认30分钟
        
        # 纯 Python 植入 TRIMP 生理负荷计算
        rest_hr, max_hr = 60, 190
        hr_reserve = max_hr - rest_hr
        hr_intensity = (hr - rest_hr) / hr_reserve if hr_reserve > 0 else 0
        
        if hr_intensity < 0.6:
            factor, zone = 1.0, "轻松 (E/Recovery)"
        elif hr_intensity < 0.75:
            factor, zone = 1.5, "中等 (Marathon)"
        elif hr_intensity < 0.88:
            factor, zone = 2.0, "较高 (Threshold)"
        else:
            factor, zone = 3.0, "高强度 (Interval/Repetition)"
            
        trimp = dur * hr_intensity * factor
        assessment = f"解析到跑表数据：距离 {dist}km, 时长 {dur}min, 平均心率 {hr}bpm。\n"
        assessment += f"生理负荷(TRIMP)计算得分: {trimp:.1f}。强度区间属于: {zone}。"
        if trimp > 150:
            assessment += " 建议接下来安排至少1-2天的轻松跑或休息。"
    else:
        # 如果正则匹配不到，就把原数据抛进 context 供大模型直接看
        assessment = "系统未能从 CSV 中精确提取出规则的数据。请依据用户提供的原始数据进行分析评估。"
        csv_start = last_message.find("【附件")
        csv_text = last_message[csv_start:csv_start+800] if csv_start != -1 else ""
        assessment += f"\n[原始数据片段]\n{csv_text}"
        
    context = f"【跑表数据解析与负荷评估】\n{assessment}"
    return {"context": context}

# 4. 定义大模型生成节点 (纯粹的合成器，不带 Tool)
def llm_node(state: AgentState):
    from pydantic import SecretStr
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("未找到 DEEPSEEK_API_KEY，请在 .env 文件中设置。")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    
    llm = ChatOpenAI(
        model="deepseek-v4-flash",
        api_key=SecretStr(api_key),
        base_url=base_url,
        temperature=0.8,
        streaming=True
    )
    
    system_msg = """你是一个极其严谨的专业中长跑智能教练。
请遵循以下回答规范：
1. **大量使用 Emoji 表情符号** 🏃‍♂️📊💪🔥，保持语气活泼、人性化，就像真正的教练在和学员沟通。
2. 你的回答需要格式极其清晰，多使用加粗、列表和引用，便于跑者在手机上快速阅读。
3. 如果系统为你注入了【跑表数据】，请在开头主动提及“我已经仔细分析了你的跑表数据...”。
4. 如果系统为你注入了【知识库检索结果】，请明确提及“根据丹尼尔斯经典训练法”。
5. **格式严禁**：在表示数字区间时（如心率 130 到 140），必须使用连字符（例如 130-140），绝对不能使用波浪号（~）。
6. **剥夺计算权**：绝对禁止你去执行乘除法运算！在给出步频、步幅和配速建议时，你必须严格引用系统前置节点算好的【VDOT配速表】和【物理验算配速结果】，比对该结果是否合理并直言不讳。如果超出常理，直接驳回，严禁自行捏造公式重新计算。
7. **短距离无氧心率滞后规则（极高优）**：当识别到距离 <= 400米或单组时间 <= 90秒的高强度冲刺圈时，严禁将冲刺圈平均心率低、而随后休息圈心率极高判定为“设备捕捉错误”。必须明确向用户解释：这是由于无氧运动的心肺响应滞后性，心率峰值必然出现在冲刺停止后的休息初期。此时应以休息圈记录到的最高心率作为该组冲刺的实际心率峰值参考。
8. **步频（SPM）强制双脚转换规则**：Coros 导出的 CSV 步频（Cadence）数据默认是单脚记录。在解析所有数据时（不论快慢配速），你必须将读取到的所有步频数值无条件 × 2，并严格使用转换后的双脚步频进行物理公式验算和专业评价。
9. **年龄基准修正**：在没有明确说明年龄的情况下，默认该用户为 20 岁的青年中长跑运动员（主攻 800m/1500m），预估最大心率（HRmax）基准锁定在 198 左右，停止使用 30 岁的大众跑者模板进行推演。
10. **间歇恢复心率的交互规则（极高优）**：由于跑表 CSV 导出通常只包含整圈的“平均心率”和“最高心率”，无法体现组间休息结束那一刻的“恢复瞬时心率”。在点评间歇/重复训练时，你必须在回答的末尾主动提问：“对了，你这几组间歇休息结束、准备起跑下一组时，手表上的实时心率大概降到多少了？” 以便引导用户补全丢失的关键生理指标。"""

    context = state.get("context", "")
    if context:
        system_msg += f"\n\n请严格结合以下系统前置注入的上下文信息来回答用户：\n{context}"
        
    # 主程批注：Sliding Window 后端滑动窗口裁剪
    raw_messages = state["messages"]
    if len(raw_messages) > 20:
        recent_messages = raw_messages[-14:]
    else:
        recent_messages = raw_messages
        
    # 构造带有 System Message 的最终对话体
    messages = [{"role": "system", "content": system_msg}] + recent_messages
    
    response = llm.invoke(messages)
    return {"messages": [response], "context": ""} # 清空 context 避免污染下一次多轮对话

# 5. 前置白盒路由函数
def route_request(state: AgentState) -> str:
    last_message = _get_last_text(state)
    
    # 明确检测到附带了 CSV 跑表数据
    if "【附件：用户上传的 Coros 跑表数据 CSV 文本】" in last_message:
        return "data_node"
        
    # 极简理论关键词路由
    keywords = ["理论", "恢复", "配速", "间歇跑", "E跑", "M跑", "T跑", "I跑", "R跑", "疲劳", "丹尼尔斯", "怎么跑", "训练法", "心率", "课表"]
    if any(k in last_message for k in keywords):
        return "rag_node"
        
    # 闲聊直接走向 LLM
    return "llm_node"

# 6. 构建图
builder = StateGraph(AgentState)
builder.add_node("math_node", math_node)
builder.add_node("rag_node", rag_node)
builder.add_node("data_node", data_node)
builder.add_node("llm_node", llm_node)

builder.add_edge(START, "math_node")
builder.add_conditional_edges("math_node", route_request)
builder.add_edge("rag_node", "llm_node")
builder.add_edge("data_node", "llm_node")
builder.add_edge("llm_node", END)

# 编译应用
def get_agent(checkpointer=None):
    return builder.compile(checkpointer=checkpointer)
