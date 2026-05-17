import os
import logging
# from openai import OpenAI  # Replaced with LangChain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from dotenv import load_dotenv
import sys

# 将 backend 根目录加入 import 搜索路径
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(script_dir, ".."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from rag.rag_service import rag_service

dotenv_path = os.path.join(script_dir, "..", ".env")
load_dotenv(dotenv_path)

# 获取日志记录器
logger = logging.getLogger(__name__)

# 使用简单的内存存储来保存对话历史 (实际生产中可以使用 Redis 等)
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

class DiagnosisService:
    def __init__(self):
        # 初始化 LangChain ChatOpenAI 模型
        self.llm = ChatOpenAI(
            model=os.getenv("LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
            openai_api_key=os.getenv("API_KEY"),
            openai_api_base=os.getenv("BASE_URL"),
            temperature=0.7,
            max_tokens=2000
        )
        
        # 加载 Prompt 模板字符串
        self.prompt_template_str = self._load_prompt_template()

        # 构建 LCEL Chain (Prompt | LLM | OutputParser)
        # 我们使用 MessagesPlaceholder 来支持对话历史插入
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个高度专业的中医AI辅诊系统。"),
            MessagesPlaceholder(variable_name="history"),
            ("human", self.prompt_template_str),
        ])

        self.chain = self.prompt | self.llm | StrOutputParser()

        # 包装 Chain 以支持历史记录
        self.chain_with_history = RunnableWithMessageHistory(
            self.chain,
            get_session_history,
            input_messages_key="user_desc",
            history_messages_key="history",
        )

    def _load_prompt_template(self) -> str:
        prompt_path = os.path.join(script_dir, "Prompt.md")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            logger.warning("未找到 Prompt.md 模板文件，将使用内置默认模板。")
            return "你是一位中医。请根据典籍 {rag_context}，患者症状 {user_desc}，和舌象 {tongue_desc} 给出辩证。"

    async def generate_diagnosis_stream(self, user_desc: str, tongue_desc: str, session_id: str = "default_user"):
        """
        组合 RAG 与大语言模型，通过流式 (Stream) 产生最终诊断结果。
        这是一个生成器函数，可以被 FastAPI 用于 Server-Sent Events (SSE)。
        """
        logger.info(f"开始生成诊断结果 (Session: {session_id})...")
        
        search_query = f"症状：{user_desc}。舌象：{tongue_desc}。"
        # 同步调用 RAG 检索
        import asyncio
        rag_results = await asyncio.to_thread(rag_service.search, search_query, top_k=3)
        
        if rag_results:
            rag_context_str = "\n\n".join([f"- {text}" for text in rag_results])
        else:
            rag_context_str = "未能从本地典籍中检索到充分的相关资料。"
        
        try:
            logger.debug(f"正在调用 LLM Chain...")
            
            # 使用包装了历史记录的 Chain 进行 astream (异步流式推断)
            response_stream = self.chain_with_history.astream(
                {
                    "rag_context": rag_context_str,
                    "user_desc": user_desc,
                    "tongue_desc": tongue_desc
                },
                config={"configurable": {"session_id": session_id}}
            )
            
            # 持续 yield 模型生成的文字块
            async for chunk in response_stream:
                if chunk:
                    yield chunk
                    
            logger.info("流式诊断生成成功完结。")
            
        except Exception as e:
            logger.error(f"调用 LLM 流式生成时发生错误: {e}")
            yield f"\n[系统错误：诊断生成中途失败 ({str(e)})]"

# 提供单例使用
diagnosis_service = DiagnosisService()
