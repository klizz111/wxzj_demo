import os
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

dotenv_path = os.path.join(script_dir, "..", ".env")
load_dotenv(dotenv_path)

# 配置路径
DATASET_DIR = "./dataset/伤寒论"       # 数据集
PERSIST_DIR = "./data/vector_db"   # RAG路径

def build_vector_database_via_api():
    # 1. 加载数据
    print(f"开始扫描目录 {DATASET_DIR} 下的 .txt 文件...")

    loader = DirectoryLoader(
        DATASET_DIR, 
        glob="**/*.txt", 
        loader_cls=TextLoader, 
        loader_kwargs={'encoding': 'utf-8'}
    )
    documents = loader.load()
    print(f"成功加载 {len(documents)} 个文件。")
    
    # 2. 文本切分
    print("正在进行文本切分...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,       
        chunk_overlap=50,     
        separators=["\n\n", "\n", "。", "！", "？", "，", ""]
    )
    docs = text_splitter.split_documents(documents)
    print(f"切分完成，共得到 {len(docs)} 个文本块。")
    
    # 3. 配置 Embedding 模型 
    print("正在配置 Embedding 模型...")
    api_embeddings = OpenAIEmbeddings(
        openai_api_base=os.getenv("EMBEDDING_API_URL"), 
        openai_api_key=os.getenv("API_KEY"),   
        model=os.getenv("EMBEDDING_MODEL")                            
    )

    # 4. 构建并存入 Chroma 数据库
    print("开始调用 API 生成向量并本地持久化...")
    vector_db = Chroma.from_documents(
        documents=docs,
        embedding=api_embeddings,
        persist_directory=PERSIST_DIR
    )
    
    print(f"✅ 向量库构建成功！已调用 API 并将结果保存在: {PERSIST_DIR}")

if __name__ == "__main__":
    build_vector_database_via_api()