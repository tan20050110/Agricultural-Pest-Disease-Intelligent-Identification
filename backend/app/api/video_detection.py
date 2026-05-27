# -*- coding: utf-8 -*-
# =============================================================================
# 视频检测 API 路由模块
# =============================================================================

import numpy as np
import cv2
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.services.detection_service import detection_service
from app.services.disease_service import disease_service

router = APIRouter(prefix="/video-detection", tags=["video-detection"])


@router.post("/realtime-frame")
async def detect_realtime_frame(
    file: UploadFile = File(...),
    confidence_threshold: float = Form(0.25),
    iou_threshold: float = Form(0.7)
):
    """
    虫害视频实时帧检测接口

    功能：
    - 接收视频播放时的单帧图片
    - 使用 YOLO 模型进行目标检测
    - 返回检测框结果（不保存到数据库）
    """
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="无法解析图片")

        result = detection_service.detect_frame_realtime(
            image=image,
            confidence_threshold=confidence_threshold,
            iou_threshold=iou_threshold
        )

        return {
            "success": True,
            "message": "检测成功",
            "data": {
                "boxes": [
                    {
                        "x1": box.x1,
                        "y1": box.y1,
                        "x2": box.x2,
                        "y2": box.y2,
                        "confidence": box.confidence,
                        "class_id": box.class_id,
                        "class_name": box.class_name,
                        "chinese_name": box.chinese_name
                    }
                    for box in result["boxes"]
                ],
                "total_objects": result["total_objects"],
                "detection_time": result["detection_time"],
                "image_width": result["image_width"],
                "image_height": result["image_height"]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"实时帧检测失败: {str(e)}")


@router.post("/disease-realtime-frame")
async def detect_disease_realtime_frame(
    file: UploadFile = File(...)
):
    """
    病害视频实时帧分类接口

    功能：
    - 接收视频播放时的单帧图片
    - 使用 ResNet50 模型进行病害分类
    - 返回 Top-5 分类结果（不保存到数据库）
    """
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="无法解析图片")

        result = disease_service.classify_frame_realtime(image=image)

        return {
            "success": True,
            "message": "分类成功",
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"实时帧分类失败: {str(e)}")
