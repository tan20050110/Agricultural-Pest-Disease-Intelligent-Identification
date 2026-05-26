# -*- coding: utf-8 -*-
# =============================================================================
# 摄像头检测服务模块
# =============================================================================
# 功能说明：
#   - 提供摄像头实时检测的核心服务
#   - 单例模式，确保全局唯一实例
#   - 线程安全的状态管理
#   - 调用 detection_service.model 进行 YOLO 推理
# =============================================================================

import time
import threading
import logging
from enum import Enum
from typing import Optional, Dict, Any

import numpy as np

from app.services.detection_service import detection_service

logger = logging.getLogger(__name__)


class DetectionStatus(str, Enum):
    """检测状态枚举"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class CameraDetectionService:
    """
    摄像头检测服务（单例模式）

    核心功能：
    1. 接收前端 Base64 图像帧
    2. 调用 YOLO 模型进行推理
    3. 线程安全的并发控制
    4. FPS 与统计信息管理
    """

    _instance: Optional['CameraDetectionService'] = None

    def __new__(cls):
        """单例模式：确保全局只有一个检测服务实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化服务（仅首次执行）"""
        if self._initialized:
            return

        # 检测状态
        self._status: DetectionStatus = DetectionStatus.STOPPED

        # 状态锁（线程安全，保护共享状态读写）
        self._lock = threading.Lock()

        # 并发控制信号量（最多 5 个并发推理请求）
        self._max_concurrent_requests: int = 5
        self._request_semaphore = threading.Semaphore(self._max_concurrent_requests)

        # 检测配置
        self._confidence_threshold: float = 0.5
        self._iou_threshold: float = 0.7
        self._model_image_size: int = 320  # 降低分辨率以提升推理速度

        # 统计信息
        self._frame_count: int = 0          # 总帧数
        self._fps_frame_count: int = 0      # FPS 计数（每秒重置）
        self._last_fps_time: float = time.time()

        self._initialized = True
        logger.info("摄像头检测服务初始化完成")

    # =========================================================================
    # 属性访问（线程安全）
    # =========================================================================

    @property
    def is_running(self) -> bool:
        """检测是否正在运行"""
        with self._lock:
            return self._status == DetectionStatus.RUNNING

    @property
    def status(self) -> DetectionStatus:
        """获取当前状态"""
        with self._lock:
            return self._status

    @status.setter
    def status(self, value: DetectionStatus):
        """设置当前状态"""
        with self._lock:
            self._status = value

    # =========================================================================
    # 核心检测方法
    # =========================================================================

    def detect_image(self, image: np.ndarray) -> Dict[str, Any]:
        """
        检测单帧图像（核心推理方法）

        参数：
            image: BGR 格式的 NumPy 数组

        返回：
            Dict 包含: boxes, frame_index, fps, detection_time, total_objects
        """
        # 使用信号量控制并发数，防止服务过载
        acquired = self._request_semaphore.acquire(timeout=5.0)
        if not acquired:
            return {
                "boxes": [],
                "frame_index": self._frame_count,
                "fps": 0.0,
                "detection_time": 0.0,
                "total_objects": 0
            }

        try:
            start_time = time.time()

            # 确保模型已加载
            if detection_service.model is None:
                detection_service._load_model_smart()

            # 调用 YOLO 模型预测
            results = detection_service.model.predict(
                source=image,
                conf=self._confidence_threshold,   # 置信度阈值
                iou=self._iou_threshold,           # IOU 阈值
                save=False,                        # 不保存文件
                imgsz=self._model_image_size,      # 推理分辨率（320 提升速度）
                half=False,                        # FP16（部分环境不支持）
                verbose=False,                     # 关闭详细输出
                stream=False                       # 非流式推理
            )

            # 解析检测框
            boxes = []
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = detection_service.class_names.get(class_id, f"class_{class_id}")
                    chinese_name = detection_service.get_class_chinese_name(class_name)
                    treatment_advice = detection_service.get_treatment_advice(class_name)

                    boxes.append({
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                        "confidence": confidence,
                        "class_id": class_id,
                        "class_name": class_name,
                        "chinese_name": chinese_name,
                        "treatment_advice": treatment_advice
                    })

            detection_time = time.time() - start_time

            # 更新统计信息
            self._frame_count += 1
            self._fps_frame_count += 1
            current_time = time.time()
            elapsed = current_time - self._last_fps_time

            # FPS 每秒更新一次
            fps = 0.0
            if elapsed >= 1.0:
                fps = self._fps_frame_count / elapsed
                self._fps_frame_count = 0
                self._last_fps_time = current_time

            return {
                "boxes": boxes,
                "frame_index": self._frame_count,
                "fps": round(fps, 1),
                "detection_time": round(detection_time, 3),
                "total_objects": len(boxes)
            }

        except Exception as e:
            logger.error(f"帧检测异常: {str(e)}", exc_info=True)
            return {
                "boxes": [],
                "frame_index": self._frame_count,
                "fps": 0.0,
                "detection_time": 0.0,
                "total_objects": 0
            }
        finally:
            self._request_semaphore.release()

    # =========================================================================
    # 生命周期管理
    # =========================================================================

    def start_detection(self,
                        confidence_threshold: float = 0.5,
                        iou_threshold: float = 0.7,
                        inference_interval: int = 2) -> bool:
        """
        启动摄像头检测

        参数：
            confidence_threshold: 置信度阈值 (0.0-1.0)
            iou_threshold: IOU 阈值 (0.0-1.0)
            inference_interval: 推理间隔（每 N 帧检测一次）

        返回：
            bool: 启动是否成功
        """
        if self.is_running:
            logger.info("检测已在运行中，更新配置")
            self.stop_detection()

        try:
            self._confidence_threshold = confidence_threshold
            self._iou_threshold = iou_threshold

            # 确保模型已加载
            if detection_service.model is None:
                detection_service._load_model_smart()

            # 重置统计
            self._frame_count = 0
            self._fps_frame_count = 0
            self._last_fps_time = time.time()

            self.status = DetectionStatus.RUNNING
            logger.info(f"摄像头检测已启动 (conf={confidence_threshold}, iou={iou_threshold})")
            return True

        except Exception as e:
            logger.error(f"启动摄像头检测失败: {str(e)}")
            self.status = DetectionStatus.ERROR
            return False

    def stop_detection(self):
        """停止摄像头检测"""
        if self.status == DetectionStatus.STOPPED:
            return

        self.status = DetectionStatus.STOPPED
        logger.info("摄像头检测已停止")

    def pause_detection(self):
        """暂停检测"""
        if self.status == DetectionStatus.RUNNING:
            self.status = DetectionStatus.PAUSED
            logger.info("摄像头检测已暂停")

    def resume_detection(self):
        """恢复检测"""
        if self.status == DetectionStatus.PAUSED:
            self.status = DetectionStatus.RUNNING
            logger.info("摄像头检测已恢复")


# =============================================================================
# 全局摄像头检测服务实例
# =============================================================================
camera_detection_service = CameraDetectionService()
