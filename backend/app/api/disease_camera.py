# -*- coding: utf-8 -*-
# =============================================================================
# 病害摄像头实时分类 API 路由
# =============================================================================

import base64
import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.disease_camera_service import disease_camera_service

cv2 = None
np = None


def _ensure_cv():
    global cv2, np
    if cv2 is None:
        import cv2 as _cv2
        cv2 = _cv2
    if np is None:
        import numpy as _np
        np = _np


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/camera/disease", tags=["camera-disease"])


class StartRequest(BaseModel):
    camera_id: int = Field(default=0, ge=0)
    confidence_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    iou_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    inference_interval: int = Field(default=2, ge=1)


@router.post("/detect")
async def detect_frame(request: dict):
    try:
        if not disease_camera_service.is_running:
            return {"success": False, "message": "摄像头分类服务未启动"}

        image_data = request.get("image")
        if not image_data:
            return {"success": False, "message": "缺少图像数据"}

        _ensure_cv()

        if "," in image_data:
            image_data = image_data.split(",")[1]

        image_bytes = base64.b64decode(image_data)
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if image is None:
            return {"success": False, "message": "图像解码失败"}

        result = disease_camera_service.classify_image(image)

        return {
            "success": True,
            "message": "分类成功",
            "data": {
                "predictions": result.get("predictions", []),
                "frame_index": result.get("frame_index", 0),
                "fps": result.get("fps", 0),
                "detection_time": result.get("detection_time", 0),
            }
        }

    except Exception as e:
        logger.error(f"病害分类异常: {e}", exc_info=True)
        return {"success": False, "message": f"分类失败: {str(e)}"}


@router.post("/start")
async def start_detection(request: StartRequest):
    try:
        success = disease_camera_service.start_detection(
            confidence_threshold=request.confidence_threshold,
            iou_threshold=request.iou_threshold,
            inference_interval=request.inference_interval
        )
        return {"success": True, "message": "分类服务已启动"} if success else {"success": False, "message": "启动失败"}
    except Exception as e:
        return {"success": False, "message": f"启动失败: {str(e)}"}


@router.post("/stop")
async def stop_detection():
    disease_camera_service.stop_detection()
    return {"success": True, "message": "分类服务已停止"}


@router.post("/pause")
async def pause_detection():
    disease_camera_service.pause_detection()
    return {"success": True, "message": "分类已暂停"}


@router.post("/resume")
async def resume_detection():
    disease_camera_service.resume_detection()
    return {"success": True, "message": "分类已恢复"}


@router.get("/status")
async def get_status():
    return {
        "success": True,
        "data": {
            "status": disease_camera_service.status.value,
            "is_running": disease_camera_service.is_running
        }
    }
