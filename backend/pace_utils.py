import math

class RunningPaceCalculator:
    """
    中长跑配速与生理负荷核心计算引擎
    """
    
    @staticmethod
    def calculate_basic_pace(distance_km: float, time_seconds: float) -> str:
        """
        [基础运动学算法]
        移植自原版 JS 代码：计算精确配速
        """
        if distance_km <= 0 or time_seconds <= 0:
            return "00:00 /km"
            
        # 先将总配速（秒/公里）进行四舍五入保留1位小数，杜绝基准脱节
        exact_seconds_per_km = time_seconds / distance_km
        seconds_per_km = round(exact_seconds_per_km, 1)
        
        res_min = int(seconds_per_km // 60)
        res_sec = round(seconds_per_km % 60, 1)
        
        # 补齐前面的 0，格式化输出
        res_sec_str = f"{res_sec:04.1f}".replace(".0", "")
        if len(res_sec_str) == 1 or ('.' not in res_sec_str and len(res_sec_str) < 2):
             res_sec_str = f"{int(res_sec):02d}"
             
        return f"{res_min}:{res_sec_str} /km"

    @staticmethod
    def load_vdot_table():
        import os
        import re
        table = {}
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "data", "daniels_vdot_45_70.txt")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            blocks = content.split("当 VDOT 等于 ")
            for block in blocks[1:]:
                lines = block.strip().split('\n')
                if not lines[0]: continue
                vdot = int(lines[0].split(" ")[0])
                data = {}
                for line in lines[1:]:
                    if "1500米标准比赛成绩为" in line:
                        m = re.search(r"(\d+):(\d+)", line)
                        if m: data["1500m"] = int(m.group(1))*60 + int(m.group(2))
                    elif "5000米标准比赛成绩为" in line:
                        m = re.search(r"(\d+):(\d+)", line)
                        if m: data["5000m"] = int(m.group(1))*60 + int(m.group(2))
                    elif "E跑配速区间为" in line:
                        m = re.search(r"(\d+:\d+/km 至 \d+:\d+/km)", line)
                        if m: data["E_pace"] = m.group(1).replace("~", "-")
                    elif "M跑配速为" in line:
                        m = re.search(r"(\d+:\d+/km)", line)
                        if m: data["M_pace"] = m.group(1)
                    elif "T跑配速为" in line:
                        m = re.search(r"(\d+:\d+/km)", line)
                        if m: data["T_pace"] = m.group(1)
                    elif "I跑配速为" in line:
                        m = re.search(r"(\d+:\d+/km)", line)
                        if m: data["I_pace"] = m.group(1)
                    elif "R跑配速为" in line:
                        data["R_pace"] = line.split("：")[1].strip()
                table[vdot] = data
        except Exception as e:
            print(f"Error loading VDOT table: {e}")
        return table

    @staticmethod
    def get_daniels_training_paces(race_distance_meters: int, race_time_seconds: int) -> dict:
        table = RunningPaceCalculator.load_vdot_table()
        if not table:
            return {"error": "无法加载 VDOT 数据表"}
            
        speed_vdot = 45
        endurance_vdot = 45
        
        if race_distance_meters <= 800:
            # 估算1500m成绩
            est_1500 = race_time_seconds * 2.2
            closest_vdot = 45
            min_diff = float('inf')
            for v, data in table.items():
                if "1500m" in data:
                    diff = abs(data["1500m"] - est_1500)
                    if diff < min_diff:
                        min_diff = diff
                        closest_vdot = v
            speed_vdot = closest_vdot
            endurance_vdot = max(45, int(round(speed_vdot - 3.5)))
        else:
            closest_vdot = 45
            min_diff = float('inf')
            for v, data in table.items():
                target_key = "1500m" if race_distance_meters < 3000 else "5000m"
                if target_key in data:
                    ref_dist = 1500 if target_key == "1500m" else 5000
                    est_time = race_time_seconds * ((ref_dist / race_distance_meters) ** 1.06)
                    diff = abs(data[target_key] - est_time)
                    if diff < min_diff:
                        min_diff = diff
                        closest_vdot = v
            endurance_vdot = closest_vdot
            speed_vdot = endurance_vdot
            
        e_vdot_data = table.get(endurance_vdot, table[45])
        s_vdot_data = table.get(speed_vdot, table[45])
        
        return {
            "Speed_VDOT": speed_vdot,
            "Endurance_VDOT": endurance_vdot,
            "E_pace": e_vdot_data.get("E_pace", ""),
            "M_pace": e_vdot_data.get("M_pace", ""),
            "T_pace": e_vdot_data.get("T_pace", ""),
            "I_pace": e_vdot_data.get("I_pace", ""),
            "R_pace": s_vdot_data.get("R_pace", "")
        }