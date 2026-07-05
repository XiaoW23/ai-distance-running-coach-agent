FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 配置 pip 清华源加速
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 拷贝依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝全部源代码 (由于 .dockerignore 中忽略了 chroma_db，这里只会拷贝代码和 data/ 文件夹)
COPY . .

# 关键构建阶段：直接触发知识库向量化，下载 HF 模型并生成 Linux 下的 chroma_db
# 确保在容器构建时就得到满血的知识库，不依赖运行时的外部挂载
RUN python rebuild_db.py

# 暴露端口
EXPOSE 8000

# 启动服务
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
