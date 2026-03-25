import os
from langchain_chroma  import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

script_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(script_dir, "..", ".env")
load_dotenv(dotenv_path)

class RAGService:
    def __init__(self):
        """
        初始化 RAG 服务，加载本地持久化的向量数据库
        """
        self.persist_dir = os.path.join(script_dir, "data", "vector_db")
        
        self.embeddings = OpenAIEmbeddings(
            openai_api_base=os.getenv("EMBEDDING_API_URL"), 
            openai_api_key=os.getenv("API_KEY"),   
            model=os.getenv("EMBEDDING_MODEL")                            
        )
        
        # 初始化 Chroma 实例
        self.vector_db = Chroma(
            persist_directory=self.persist_dir,
            embedding_function=self.embeddings
        )

    def search(self, query: str, top_k: int = 3, related_threshold: float = 0.8):
        """
        根据 query 检索最相关的文档块
        :param query: 用户问题或检索内容
        :param top_k: 返回相关度最高的文档数量
        :return: 相关的文本列表
        """
        docs = self.vector_db.similarity_search_with_score(query, k=top_k)
        
        validate_docs = []
        for doc, score in docs:
            if score >= related_threshold:
                validate_docs.append(doc)
                
        return validate_docs
rag_service = RAGService()
