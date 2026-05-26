# -*- coding: utf-8 -*-
# =============================================================================
# 摄像头检测 API 路由模块
# =============================================================================
# 功能说明：
#   - 接收前端摄像头采集的 Base64 图像帧
#   - 调用摄像头检测服务进行 YOLO 推理
#   - 返回检测框坐标、类别、置信度等结果
#
# API 接口列表：
#   POST /api/camera/detect   - 单帧检测
#   POST /api/camera/start    - 启动检测服务
#   POST /api/camera/stop     - 停止检测服务
#   POST /api/camera/pause    - 暂停检测
#   POST /api/camera/resume   - 恢复检测
#   GET  /api/camera/status   - 获取检测状态
# =============================================================================

import base64
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.camera_detection_service import camera_detection_service

# 延迟导入重型依赖
cv2 = None
np = None


def _ensure_cv_imports():
    """延迟导入 OpenCV 和 NumPy"""
    global cv2, np
    if cv2 is None:
        import cv2 as _cv2
        cv2 = _cv2
    if np is None:
        import numpy as _np
        np = _np


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/camera", tags=["camera"])


# =============================================================================
# 请求/响应模型
# =============================================================================

class StartDetectionRequest(BaseModel):
    """启动检测请求"""
    camera_id: int = Field(default=0, ge=0, description="摄像头设备ID")
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="置信度阈值")
    iou_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="IOU阈值")
    inference_interval: int = Field(default=2, ge=1, description="推理间隔")


class DetectFrameRequest(BaseModel):
    """单帧检测请求"""
    image: str = Field(..., description="Base64 编码的图像数据")


# =============================================================================
# 单帧检测接口
# =============================================================================

@router.post("/detect")
async def detect_frame(request: dict):
    """
    接收前端发送的图像帧并返回检测结果

    请求体：
        {"image": "data:image/jpeg;base64,..."}

    返回：
        {
            "success": true,
            "message": "检测成功",
            "data": {
                "boxes": [...],
                "frame_index": 1,
                "fps": 15.2,
                "detection_time": 0.125,
                "total_objects": 3
            }
        }
    """
    try:
        # 检查检测服务状态
        if not camera_detection_service.is_running:
            return {
                "success": False,
                "message": "摄像头检测未启动，请先调用 /camera/start"
            }

        # 获取图像数据
        image_data = request.get("image")
        if not image_data:
            return {"success": False, "message": "缺少图像数据"}

        _ensure_cv_imports()

        # 移除 data:image 前缀（如 "data:image/jpeg;base64,"）
        if "," in image_data:
            image_data = image_data.split(",")[1]

        # Base64 解码
        image_bytes = base64.b64decode(image_data)
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if image is None:
            return {"success": False, "message": "图像解码失败"}

        # 调用检测服务进行推理
        result = camera_detection_service.detect_image(image)

        return {
            "success": True,
            "message": "检测成功",
            "data": {
                "boxes": result.get("boxes", []),
                "frame_index": result.get("frame_index", 0),
                "fps": result.get("fps", 0),
                "detection_time": result.get("detection_time", 0),
                "total_objects": result.get("total_objects", 0)
            }
        }

    except Exception as e:
        logger.error(f"图像检测异常: {str(e)}", exc_info=True)
        return {"success": False, "message": f"图像检测失败: {str(e)}"}


# =============================================================================
# 状态控制接口
# =============================================================================

@router.post("/start")
async def start_detection(request: StartDetectionRequest):
    """
    启动摄像头检测服务

    功能：配置检测参数并启动检测
    """
    try:
        success = camera_detection_service.start_detection(
            confidence_threshold=request.confidence_threshold,
            iou_threshold=request.iou_threshold,
            inference_interval=request.inference_interval
        )

        if success:
            return {"success": True, "message": "检测服务已启动"}
        else:
            return {"success": False, "message": "检测服务启动失败"}

    except Exception as e:
        logger.error(f"启动检测服务异常: {str(e)}")
        return {"success": False, "message": f"启动失败: {str(e)}"}


@router.post("/stop")
async def stop_detection():
    """停止摄像头检测服务"""
    camera_detection_service.stop_detection()
    return {"success": True, "message": "检测服务已停止"}


@router.post("/pause")
async def pause_detection():
    """暂停摄像头检测"""
    camera_detection_service.pause_detection()
    return {"success": True, "message": "检测已暂停"}


@router.post("/resume")
async def resume_detection():
    """恢复摄像头检测"""
    camera_detection_service.resume_detection()
    return {"success": True, "message": "检测已恢复"}


@router.get("/status")
async def get_detection_status():
    """获取当前检测状态"""
    return {
        "success": True,
        "data": {
            "status": camera_detection_service.status.value,
            "is_running": camera_detection_service.is_running
        }
    }
