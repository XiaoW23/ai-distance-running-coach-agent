import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# We will initialize Chroma DB here. It's a singleton-like setup for simplicity.
CHROMA_DB_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

_vectorstore = None

def get_vectorstore():
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore
        
    # 使用本地开源 HuggingFace 嵌入模型（支持中文效果更好的 text2vec-base-chinese）
    # 初次运行会自动下载模型权重
    embeddings = HuggingFaceEmbeddings(
        model_name="shibing624/text2vec-base-chinese"
    )
    
    # Check if DB already exists
    if os.path.exists(CHROMA_DB_DIR) and os.listdir(CHROMA_DB_DIR):
        _vectorstore = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
        return _vectorstore
    
    # If not, load ALL documents from data directory and build the DB
    if not os.path.exists(DATA_DIR):
        raise FileNotFoundError(f"Knowledge base directory not found at {DATA_DIR}")
        
    # 使用 DirectoryLoader 加载 data 文件夹下的所有 txt 文件
    loader = DirectoryLoader(DATA_DIR, glob="**/*.txt", loader_cls=TextLoader, loader_kwargs={'encoding': 'utf-8'})
    docs = loader.load()
    
    if not docs:
        raise ValueError("No documents found in the knowledge base directory.")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        separators=["\n\n", "\n", "。", "！", "？", " ", ""]
    )
    splits = text_splitter.split_documents(docs)
    
    _vectorstore = Chroma.from_documents(
        documents=splits, 
        embedding=embeddings, 
        persist_directory=CHROMA_DB_DIR
    )
    return _vectorstore

def retrieve_knowledge(query: str, k: int = 3):
    """Retrieve top k relevant chunks from the running formula knowledge base."""
    vectorstore = get_vectorstore()
    results = vectorstore.similarity_search(query, k=k)
    return "\n\n".join([res.page_content for res in results])
