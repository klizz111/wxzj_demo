import os
import sys
import logging
from dotenv import load_dotenv

script_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(script_dir, "..", ".env")
load_dotenv(dotenv_path)

# 全局日志配置，优先从环境变量读取
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.info(f"测试脚本启动，当前日志级别: {LOG_LEVEL}")

# 将 backend 根目录加入 import 搜索路径，确保可以被正确导入
backend_dir = os.path.abspath(os.path.join(script_dir, ".."))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from vision.vision_service import vision_service

def run_test(image_path: str):
    print(f"开始测试，检查图片路径: {image_path}")
    if not os.path.exists(image_path):
        print("❌ 错误: 找不到该图片文件，请检查路径是否正确。")
        return

    print("✅ 找到图片，正在读取...")
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    print("🚀 正在请求 Vision API 进行图像解析，请稍候...")
    result = vision_service.analyze_tongue(image_bytes)
    
    print("\n" + "="*40)
    print("✨ 服务返回的诊断结果:")
    print("="*40)
    print(result)
    print("="*40 + "\n")

if __name__ == "__main__":
    # 默认寻找当前目录下的 test_tongue.jpg 文件进行测试
    default_test_image = os.path.join(script_dir, "test","test01.png")
    
    # 允许通过命令行传入指定的图片，例如: python test_vision.py /absolute/path/to/image.jpg
    target_image = sys.argv[1] if len(sys.argv) > 1 else default_test_image
    
    if len(sys.argv) == 1:
        print(f"提示: 未通过命令行指定图片路径，将默认使用: {target_image}")
        print("你也可以像这样指定路径执行测试：python test_vision.py <你的本地图片路径>\n")
        
    run_test(target_image)
