import os
import sys
import logging
from dotenv import load_dotenv

script_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(script_dir, "..", ".env")
load_dotenv(dotenv_path)

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.DEBUG),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

backend_dir = os.path.abspath(os.path.join(script_dir, ".."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from diagnosis.diagnosis_service import diagnosis_service
from vision.vision_service import vision_service

def test_workflow():
    print("="*50)
    print("🧠 开始测试 端到端 (Vision + RAG + LLM) 组合工作流")
    print("="*50)
    
    fake_user_desc = "最近几天老是头痛，怕风，身上出汗但觉得冷，没胃口。"
    
    # 尝试加载真实图片作为测试（默认寻找你之前用的 test01.png）
    # 如果找不到，就退回到 mock 的默认文本
    test_image_path = os.path.join(script_dir, "..", "services", "test", "test01.png")
    
    if os.path.exists(test_image_path):
        print(f"✅ 找到舌诊测试图片: {test_image_path}")
        print("正在调用 Vision 大模型解析舌诊图片 (这可能需要几秒钟)...")
        with open(test_image_path, "rb") as f:
            image_bytes = f.read()
        tongue_desc = vision_service.analyze_tongue(image_bytes)
    else:
        print(f"⚠️ 未找到舌诊测试图片 ({test_image_path})，使用模拟舌诊数据。")
        tongue_desc = "舌质淡红，舌苔薄白，无明显裂纹或齿痕。"
    
    print("-" * 50)
    print(f"👤 患者自述: {fake_user_desc}")
    print(f"👅 舌诊解析: \n{tongue_desc}")
    print("-" * 50)
    print("正在进行 RAG 检索并调用 LLM 生成流式诊断，请稍候...\n")
    
    print("="*50)
    print("✨ AI 中医诊断结果:")
    print("="*50)
    
    # 消费生成器中的数据
    for chunk in diagnosis_service.generate_diagnosis_stream(fake_user_desc, tongue_desc):
        # 让内容在终端能一个字一个字蹦出来
        print(chunk, end="", flush=True)
        
    print("\n" + "="*50)

if __name__ == "__main__":
    test_workflow()