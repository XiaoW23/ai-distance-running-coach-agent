import os
import shutil
from backend.rag import get_vectorstore, CHROMA_DB_DIR

if __name__ == "__main__":
    print("=========================================")
    print("    正在重建知识库向量索引...")
    print("=========================================\n")
    
    if os.path.exists(CHROMA_DB_DIR):
        print(f"发现旧的数据库缓存，正在清理: {CHROMA_DB_DIR}")
        try:
            shutil.rmtree(CHROMA_DB_DIR)
            print("清理完成。\n")
        except Exception as e:
            print(f"清理失败: {e}\n请确保没有其他程序（如 uvicorn）正在占用该文件夹，或者手动删除 chroma_db 文件夹。")
            exit(1)
            
    print("开始重新读取 data 文件夹下的所有 txt 文件，并调用本地 Embedding 模型...")
    try:
        # 这会触发 rag.py 中的加载和持久化逻辑，初次运行会自动下载 huggingface 模型权重
        get_vectorstore()
        print("\n重建成功！知识库已更新。您可以重新启动 uvicorn 服务进行测试了。")
    except Exception as e:
        print(f"\n重建失败！出现以下错误:\n{e}")
