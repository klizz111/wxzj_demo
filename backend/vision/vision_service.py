import os
import base64
from openai import AsyncOpenAI
import httpx
from dotenv import load_dotenv

import logging

script_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(script_dir, "..", ".env")
load_dotenv(dotenv_path)

# 获取日志记录器
logger = logging.getLogger(__name__)

class VisionService:
    def __init__(self):
        # 读取 .env 的 BASE_URL (https://api.siliconflow.cn/v1) 和 API_KEY
        self.client = AsyncOpenAI(
            api_key=os.getenv("API_KEY"),
            base_url=os.getenv("BASE_URL")
        )
        
        # 将环境变量中 VISUAL_MODEL 作为 Vision 调用的模型，兼容容错
        self.model = os.getenv("VISUAL_MODEL", "Pro/Qwen/Qwen2-VL-7B-Instruct")

    def _encode_image(self, image_bytes: bytes) -> tuple:
        """
        判断图片类型并将二进制图片转为 base64 字符串
        返回 (mime_type, base64_str)
        """
        # 简单判断图片头
        mime_type = "image/jpeg"
        if image_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
            mime_type = "image/png"
        elif image_bytes.startswith(b'GIF87a') or image_bytes.startswith(b'GIF89a'):
            mime_type = "image/gif"
        
        return mime_type, base64.b64encode(image_bytes).decode('utf-8')

    async def analyze_tongue(self, image_bytes: bytes) -> str:
        """
        舌诊图片解析
        :param image_bytes: 舌头图片的二进制数据
        :return: 中医分析的结果文本
        """
        if not image_bytes:
            return "无图片，忽略舌诊信息。"

        mime_type, base64_image = self._encode_image(image_bytes)
        
        # 读取 Prompt.md 
        prompt_path = os.path.join(script_dir, "Prompt.md")
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_text = f.read().strip()

        try:
            logger.debug(f"正在尝试调用模型: {self.model}，图片格式: {mime_type}")
            # 采用 OpenAI 兼容格式发送多模态求情
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                extra_body={"enable_thinking": False}
            )
            logger.debug(f"API 原始响应对象: {response}")
            return response.choices[0].message.content.strip() if response.choices[0].message.content else "返回了空字符串，请检查模型支持性或图片内容。"
        except Exception as e:
            logger.error(f"Vision 解析遇到错误: {e}")
            return f"舌诊图片解析失败: {str(e)}"

vision_service = VisionService()
