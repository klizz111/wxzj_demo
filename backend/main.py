from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.diagnosis import router as diagnosis_router
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# 全局日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
logger.info(f"应用启动，当前日志级别: {LOG_LEVEL}")

app = FastAPI(
    title="五行知己",
    description="基于 FastAPI + LangChain + RAG 的中医诊疗多模态系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(diagnosis_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "System is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
