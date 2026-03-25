import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

dotenv_path = os.path.join(script_dir, "..", ".env")
load_dotenv(dotenv_path)

PERSIST_DIR = "./data/vector_db"

def test_vector_db():
    print("正在配置 Embedding 模型...")
    api_embeddings = OpenAIEmbeddings(
        openai_api_base=os.getenv("EMBEDDING_API_URL"), 
        openai_api_key=os.getenv("API_KEY"),   
        model=os.getenv("EMBEDDING_MODEL")                            
    )

    print(f"正在加载本地向量数据库: {PERSIST_DIR} ...")
    vector_db = Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=api_embeddings
    )

    test_queries = [
        "太阳病的主要症状和脉象表现是什么？", 
        "病身为痉、湿、暍这三种病症各有什么特征？",
        "empty message"
    ]

    print("\n" + "="*45)
    
    for i, query in enumerate(test_queries, 1):
        print(f"🔍 测试问题 {i}: 【{query}】")
        
        results = vector_db.similarity_search_with_score(query, k=2)
        
        if not results:
            print("  -> ⚠️ 未检索到相关内容。\n")
            continue
            
        for rank, (doc, score) in enumerate(results, 1):
            print(f"  {rank}. 相关度得分: {score:.4f}")
            if score < 0.75:
                print("     ⚠️ 相关度较低，pass")
                pass
            else:
                print(f"     文档元数据: {doc.metadata}")
                print(f"     文档内容: {doc.page_content[:]}\n") 
        print("\n" + "-"*50 + "\n")
            
        print("-" * 50)

if __name__ == "__main__":
    test_vector_db()