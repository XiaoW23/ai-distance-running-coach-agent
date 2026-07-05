from langchain_core.tools import tool
from backend.rag import retrieve_knowledge

@tool
def retrieve_running_knowledge(query: str) -> str:
    """
    检索《丹尼尔斯经典跑步训练法》知识库。
    如果你需要了解训练理论、配速含义（E/M/T/I/R）、或者负荷恢复原则，请使用此工具。
    输入参数 query 应该是针对你想要了解的具体问题或关键词，例如 "间歇跑的作用" 或 "连续疲劳怎么办"。
    """
    try:
        return retrieve_knowledge(query)
    except Exception as e:
        return f"检索知识库时出错: {str(e)}"

@tool
def calculate_training_load(distance_km: float, duration_min: float, avg_heart_rate: int) -> str:
    """
    计算单次跑步训练的生理负荷（TRIMP 简化版）。
    输入参数：
    - distance_km: 跑步距离（公里）
    - duration_min: 跑步时长（分钟）
    - avg_heart_rate: 平均心率（次/分钟）
    
    返回：
    关于本次训练负荷的评估描述，供后续分析参考。
    """
    # 极简的心率负荷计算（仅作演示）：
    # 假设静息心率60，最大心率190
    rest_hr = 60
    max_hr = 190
    
    if avg_heart_rate <= rest_hr:
        return "平均心率异常低，无法计算有效负荷。"
        
    hr_reserve = max_hr - rest_hr
    hr_intensity = (avg_heart_rate - rest_hr) / hr_reserve
    
    # 简单系数
    if hr_intensity < 0.6:
        intensity_factor = 1.0
        intensity_zone = "轻松"
    elif hr_intensity < 0.75:
        intensity_factor = 1.5
        intensity_zone = "中等"
    elif hr_intensity < 0.88:
        intensity_factor = 2.0
        intensity_zone = "较高 (阈值)"
    else:
        intensity_factor = 3.0
        intensity_zone = "高强度 (间歇/无氧)"
        
    trimp = duration_min * hr_intensity * intensity_factor
    
    assessment = f"本次训练TRIMP(冲量)得分约为: {trimp:.1f}。强度区间属于: {intensity_zone}。"
    if trimp > 150:
        assessment += " 这是一次非常高负荷的训练，建议接下来安排至少1-2天的轻松跑或休息。"
    elif trimp > 80:
        assessment += " 这是一次中高负荷训练，身体受到了一定刺激。"
    else:
        assessment += " 训练负荷较轻，适合作为恢复或基础积累。"
        
    return assessment
