# 🏃‍♂️ AI 中长跑训练教练智能体 (Distance Running Coach Agent)

基于《丹尼尔斯经典跑步训练法》打造的专业级中长跑训练辅助工具。结合 LangGraph 的强力状态机编排与 DeepSeek 大语言模型的逻辑推理，为大众跑者提供科学的配速规划、跑表数据智能解析与定制化课表调整。

---

## ✨ 核心特性 (Features)

### 🧠 专业级大模型智能体 (AI Agent)
- **跑力换算引擎 (VDOT Calculator)**：内置丹尼尔斯 VDOT 公式计算工具，有效避免通用大模型的“算数崩塌”幻觉，精准提供 E(轻松)/M(马拉松)/T(乳酸门槛)/I(间歇)/R(重复) 五个强度的绝对配速区间。
- **多设备 CSV 数据联合解析 (Multi-CSV Parsing)**：支持一次性上传多份跑表数据（如热身跑+间歇主课），后端具备文件级作用域隔离 (File-Level Scope) 能力，单独判定每段数据的单双脚步频与特征，彻底杜绝数据串台误判。
- **运动生理学专家 Prompt**：内建防幻觉提示词，强行矫正模型在无氧心率滞后、单双脚步频转换等专业领域的认知偏差。

### 🔄 商业级交互机制 (Interactive UX)
- **上下文回滚 (Edit & Retry)**：在历史气泡中点击编辑，修改保存后，后端通过 LangGraph 的 `RemoveMessage` 机制精准清除脏数据，恢复纯净状态机，实现完美“时间漫游”。
- **单键重试 (Regenerate)**：极简的刷新功能，全自动追溯最后一条提问，一键擦除上一轮失败回答并利用流式输出重新生成。
- **右侧单轮时间轴 (Timeline Navigation)**：长对话自动生成历史锚点，支持随时一键跳转至上下文关键处。
- **无感并发起名 (Auto Title)**：发问时后台无缝调用轻量级 LLM 生成标题并更新 SQLite，全程无感刷新。

### 🎨 极致的现代化 UI 体验 (Glassmorphism & Dark Mode)
- **全局深浅色切换 (Day/Night Theme)**：内建 macOS 级深空渐变底色与极低透明度超透玻璃质感 (Ultra-Clear Glassmorphism)，支持系统偏好探查与一键平滑无损切换。
- **胶囊化文件交互 (File Pills UI)**：多附件上传时提供直观的文件胶囊展示，带来精巧质感。
- **响应式动态侧边栏**：支持大屏幕的折叠伸缩交互，适配各种桌面和移动端分辨率，兼顾美感与效能。

---

## 🛠️ 技术架构 (Tech Stack)

- **前端 (Frontend)**：HTML5 + Vanilla JS + Tailwind CSS (零框架，纯享极致性能)
- **后端 (Backend)**：FastAPI + Uvicorn (异步协程，完美处理高并发 SSE)
- **编排与推理层 (Agent)**：LangGraph + LangChain + DeepSeek-Chat API
- **数据持久化 (Database)**：SQLite (`AsyncSqliteSaver` 物理落盘与 `user_sessions` 关系表)
- **部署发布 (Deployment)**：支持 Docker 容器化跨平台部署。

---

## 🚀 快速启动 (Quick Start)

### 方式一：Docker 一键部署（推荐）

请确保本机已安装 [Docker](https://www.docker.com/)，本项目遵循“不可变基础设施”理念，已实现完整容器化。在项目根目录下执行以下命令：

**配置环境变量**：先将根目录的 `.env.example` 重命名为 `.env`，填入您的 DeepSeek API 秘钥（无需加双引号）：
```env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_BASE_URL=[https://api.deepseek.com/v1](https://api.deepseek.com/v1)
```

构建包含原生知识库的镜像（构建阶段会自动下载模型并生成干净的 RAG 向量数据库）：
```bash
docker build -t ai-running-coach:v1 .
```

注入环境变量并启动服务：
```bash
docker run -d -p 8000:8000 --env-file .env --name my-coach ai-running-coach:v1
```

启动成功后，打开浏览器访问：http://localhost:8000 即可使用！

### 方式二：本地 Python 环境启动

#### 1. 环境准备
请确保本机已安装 Python 3.10+ 环境。克隆本仓库到本地。

#### 2. 配置环境变量
在项目根目录新建或修改 `.env` 文件，填入您的 DeepSeek API 密钥：
```env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_BASE_URL=[https://api.deepseek.com/v1](https://api.deepseek.com/v1)
```

#### 3. 安装依赖
```bash
pip install -r requirements.txt
```

#### 4. 启动服务
双击运行根目录下的 `start.bat`，或者在终端中执行：
```bash
uvicorn backend.main:app --reload
```
服务启动后，打开浏览器访问：[http://localhost:8000](http://localhost:8000) 即可开始您的专属训练！

---

## 📂 项目结构 (Project Structure)
```text
.
├── backend/
│   ├── main.py       # FastAPI 路由控制器与并发任务中心
│   ├── agent.py      # LangGraph 状态机编排与记忆挂载
│   └── tools.py      # VDOT 计算器与 CSV 数据解析器
├── frontend/
│   └── index.html    # 现代化深浅色玻璃拟态 UI 核心逻辑
├── Dockerfile        # 容器化构建脚本
├── requirements.txt
├── .env
└── start.bat
```
