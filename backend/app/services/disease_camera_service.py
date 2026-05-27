# -*- coding: utf-8 -*-
# =============================================================================
# 病害摄像头实时分类服务
# =============================================================================

import time
import threading
import logging
from enum import Enum
from typing import Optional, Dict, Any

import numpy as np

from app.services.disease_service import disease_service

logger = logging.getLogger(__name__)


class DetectionStatus(str, Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class DiseaseCameraService:

    _instance: Optional['DiseaseCameraService'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._status: DetectionStatus = DetectionStatus.STOPPED
        self._lock = threading.Lock()
        self._max_concurrent_requests: int = 5
        self._request_semaphore = threading.Semaphore(self._max_concurrent_requests)
        self._confidence_threshold: float = 0.3
        self._frame_count: int = 0
        self._fps_frame_count: int = 0
        self._last_fps_time: float = time.time()

        self._initialized = True
        logger.info("病害摄像头分类服务初始化完成")

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._status == DetectionStatus.RUNNING

    @property
    def status(self) -> DetectionStatus:
        with self._lock:
            return self._status

    @status.setter
    def status(self, value: DetectionStatus):
        with self._lock:
            self._status = value

    def start_detection(self, confidence_threshold: float = 0.3, iou_threshold: float = 0.7, inference_interval: int = 2) -> bool:
        with self._lock:
            if self._status == DetectionStatus.RUNNING:
                return True
            self._confidence_threshold = confidence_threshold
            self._frame_count = 0
            self._fps_frame_count = 0
            self._last_fps_time = time.time()
            self._status = DetectionStatus.RUNNING
            logger.info("病害摄像头分类服务已启动")
            return True

    def stop_detection(self):
        with self._lock:
            self._status = DetectionStatus.STOPPED
            logger.info("病害摄像头分类服务已停止")

    def pause_detection(self):
        with self._lock:
            if self._status == DetectionStatus.RUNNING:
                self._status = DetectionStatus.PAUSED

    def resume_detection(self):
        with self._lock:
            if self._status == DetectionStatus.PAUSED:
                self._status = DetectionStatus.RUNNING

    def classify_image(self, image: np.ndarray) -> Dict[str, Any]:
        acquired = self._request_semaphore.acquire(timeout=5.0)
        if not acquired:
            return {"predictions": [], "frame_index": self._frame_count, "fps": 0.0, "detection_time": 0.0}

        try:
            start_time = time.time()
            self._frame_count += 1

            if disease_service.model is None:
                disease_service._load_model()

            import torch
            import cv2

            img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            img_tensor = disease_service.transform(img_rgb).unsqueeze(0).to(disease_service.device)

            with torch.no_grad():
                output = disease_service.model(img_tensor)
                probs = torch.softmax(output, dim=1)

            predictions = disease_service._get_disease_prediction(probs, top_k=3)

            detection_time = time.time() - start_time

            # FPS 计算
            self._fps_frame_count += 1
            elapsed = time.time() - self._last_fps_time
            fps = self._fps_frame_count / elapsed if elapsed >= 1.0 else 0.0
            if elapsed >= 1.0:
                self._fps_frame_count = 0
                self._last_fps_time = time.time()

            return {
                "predictions": [
                    {"class_name": p.class_name, "chinese_name": p.chinese_name,
                     "confidence": p.confidence, "crop": p.crop, "disease": p.disease}
                    for p in predictions
                ],
                "frame_index": self._frame_count,
                "fps": round(fps, 1),
                "detection_time": round(detection_time, 3)
            }

        except Exception as e:
            logger.error(f"病害分类异常: {e}")
            return {"predictions": [], "frame_index": self._frame_count,
                    "fps": 0.0, "detection_time": 0.0}
        finally:
            self._request_semaphore.release()


disease_camera_service = DiseaseCameraService()
