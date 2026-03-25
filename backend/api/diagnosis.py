import logging
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional

# 导入我们的核心服务
from vision.vision_service import vision_service
from diagnosis.diagnosis_service import diagnosis_service

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["diagnosis"]
)

@router.post("/chat/diagnosis")
async def diagnose(
    description: str = Form(..., description="患者口述症状"),
    image: Optional[UploadFile] = File(None, description="患者舌诊图片"),
    stream: bool = Form(False, description="是否开启流式输出")
):
    """
    接收前端传来的图片和文本症状，返回中医诊断结果。
    如果 stream=True，将返回流式 (Server-Sent Events) 响应。
    """
    logger.info(f"收到诊断请求，描述内容长度: {len(description)}, 是否包含图片: {image is not None}, 是否流式: {stream}")

    # 1. 尝试解析图像 (舌诊)
    tongue_desc = "未提供舌图，无舌诊信息。"
    if image is not None:
        try:
            image_bytes = await image.read()
            # 调用 Vision 接口解析
            tongue_desc = vision_service.analyze_tongue(image_bytes)
            logger.info("视觉解析完成")
        except Exception as e:
            logger.error(f"图像读取或解析失败: {e}")
            tongue_desc = "图片处理错误，未能获取舌诊信息。"

    # 2. 根据用户选择返回流式或阻塞式结果
    if stream:
        import asyncio
        # 定义一个异步生成器供 StreamingResponse 消费
        async def streamed_response():
            # 先给前端吐出一句系统提示
            yield "【系统提示】已收到您的舌图和症状，正在结合典籍分析中...\n\n"
            
            # 由于 LLM 本身是同步迭代生成器，我们使用 for 循环包裹
            for chunk in diagnosis_service.generate_diagnosis_stream(description, tongue_desc):
                yield chunk
                # 让出控制权，确保 Uvicorn 有机会把当前 chunk 发送到网络缓冲
                # 同时制造细微延迟以增强前端纯视觉的打字机流式效果
                await asyncio.sleep(0.02)
                
        # 返回流式响应，Content-Type 使用 text/event-stream 或 text/plain
        # 必须带上 Cache-Control 等相关的 headers 避免前端或代理将其完全缓冲
        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
        return StreamingResponse(streamed_response(), media_type="text/event-stream", headers=headers)
    
    else:
        # 如果不是流式，我们需要将生成器里的内容全接收完再返回
        # （因为我们刚才把代码全改成了 generator，这里做个简单兼容）
        full_text = ""
        for chunk in diagnosis_service.generate_diagnosis_stream(description, tongue_desc):
            full_text += chunk
            
        return {
            "status": "success",
            "data": {
                "tongue_analysis": tongue_desc,
                "diagnosis_result": full_text
            }
        }
