# 🏃‍♂️ AI 中长跑训练教练智能体 (Distance Running Coach Agent)

基于《丹尼尔斯经典跑步训练法》打造的专业级中长跑训练辅助工具。结合 LangGraph 的强力状态机编排与 DeepSeek 大语言模型的逻辑推理，为大众跑者提供科学的配速规划、跑表数据智能解析与定制化课表调整。

---

## ✨ 核心特性 (Features)

### 🧠 专业级大模型智能体 (AI Agent)
- **跑力换算引擎 (VDOT Calculator)**：内置丹尼尔斯 VDOT 公式计算工具，有效避免通用大模型的“算数崩塌”幻觉，精准提供 E(轻松)/M(马拉松)/T(乳酸门槛)/I(间歇)/R(重复) 五个强度的绝对配速区间。
- **本地跑表数据解析 (CSV Parser)**：支持用户直接拖拽上传 Coros (高驰)、Garmin (佳明) 等主流跑表导出的 CSV 运动记录，AI 教练能够洞察步频、心率、心率漂移等关键生理指标，并针对性纠正训练误区。
- **运动生理学专家 Prompt**：内建防幻觉提示词，强行矫正模型在无氧心率滞后、单双脚步频转换等专业领域的认知偏差。

### 🔄 商业级 Time Travel 交互机制 (交互降维打击)
- **上下文回滚 (Edit & Retry)**：在历史气泡中点击编辑，支持将长文本转换为自适应拉伸的编辑卡片。修改保存后，后端通过 LangGraph 的 `RemoveMessage` 机制精准狙击并彻底清除脏数据，恢复纯净状态机，实现完美“时间漫游”。
- **单键重试 (Regenerate)**：极简的刷新功能，全自动追溯最后一条提问，一键擦除上一轮失败回答并利用流式输出重新生成，告别复杂的上下文污染。
- **无感并发起名 (Auto Title)**：用户发出首句提问时，底层启动并发协程，调用轻量级 LLM 生成精简 10 字标题并直接写入 SQLite，毫无卡顿，全自动更新侧边栏。

### 🎨 极致的现代化 UI 体验 (Glassmorphism UX)
- 玻璃拟态设计，原生平滑滚动 (`behavior: 'smooth'`)，搭配双重延时置底，杜绝闪烁。
- SSE 动态打字机流式响应体验。
- 空状态时的动态居中欢迎屏 (Welcome Screen) 无缝转场。

---

## 🛠️ 技术架构 (Tech Stack)

- **前端 (Frontend)**：HTML5 + Vanilla JS + Tailwind CSS (零框架，纯享极致性能)
- **后端 (Backend)**：FastAPI + Uvicorn (异步协程，完美处理高并发 SSE)
- **编排与推理层 (Agent)**：LangGraph + LangChain + DeepSeek-Chat API
- **数据持久化 (Database)**：SQLite (`AsyncSqliteSaver` 物理落盘与 `user_sessions` 关系表)

---

## 🚀 快速启动 (Quick Start)

### 1. 环境准备
请确保本机已安装 Python 3.10+ 环境。克隆本仓库到本地。

### 2. 配置环境变量
在项目根目录新建或修改 `.env` 文件，填入您的 DeepSeek API 密钥：
```env
DEEPSEEK_API_KEY=sk-xxxxxxxxx
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 启动服务
双击运行根目录下的 `start.bat`，或者在终端中执行：
```bash
uvicorn backend.main:app --reload
```
服务启动后，打开浏览器访问：[http://localhost:8000](http://localhost:8000) 即可开始您的专属训练！

---

## 📂 项目结构 (Project Structure)
```
.
├── backend/
│   ├── main.py       # FastAPI 路由控制器与并发任务中心
│   ├── agent.py      # LangGraph 状态机编排与记忆挂载
│   └── tools.py      # VDOT 计算器与 CSV 数据解析器
├── frontend/
│   └── index.html    # 现代化玻璃拟态 UI 核心逻辑
├── requirements.txt
├── .env
└── start.bat
```
