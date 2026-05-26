# =============================================================================
# 病害识别 API 路由模块
# =============================================================================
# 功能说明：
#   - 定义病害识别相关的 API 接口
#   - 处理图片上传、病害分类请求、结果返回
#   - 提供可检测病害类别查询接口
#
# API 接口列表：
#   POST /api/disease/single      - 单图病害识别
#   GET  /api/disease/targets/list - 获取病害类别列表
# =============================================================================

import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response

from app.services.disease_service import disease_service
from app.services.minio_service import minio_service
from app.utils.file_utils import save_upload_file, ensure_directories
from app.config import settings
from app.models.schemas import (
    DiseaseResponse,
    DiseasePrediction,
    TargetListResponse,
    TargetItem,
)

router = APIRouter(prefix="/disease", tags=["disease"])
ensure_directories()


# =============================================================================
# 单图病害识别接口
# =============================================================================

@router.post("/single", response_model=DiseaseResponse)
async def classify_single_image(
    file: UploadFile = File(...),
    model_name: str = Form("resnet50-disease"),
    user_id: str = Form(None),
):
    """
    单图病害分类接口

    功能：
    - 接收用户上传的农作物图片
    - 使用 ResNet50 模型进行病害分类
    - 返回 Top-5 预测结果

    参数：
        file: 上传的图片文件
        model_name: 模型名称（默认 resnet50-disease）
        user_id: 用户 ID（可选）

    返回：
        DiseaseResponse: 包含分类结果的响应
    """
    try:
        os.makedirs(settings.upload_dir, exist_ok=True)
        filename = await save_upload_file(file, settings.upload_dir)
        image_path = os.path.join(settings.upload_dir, filename)

        result = disease_service.classify_single_image(
            image_path, user_id, model_name, minio_service
        )

        try:
            os.remove(image_path)
        except Exception:
            pass

        return DiseaseResponse(
            success=True,
            message="病害识别成功",
            data=result,
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"模型文件未找到: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"病害识别失败: {str(e)}")


# =============================================================================
# 病害类别列表接口
# =============================================================================

@router.get("/targets/list", response_model=TargetListResponse)
async def get_disease_target_list():
    """
    获取可识别的病害类别列表

    返回：
        TargetListResponse: 病害类别列表
    """
    targets = []
    for idx, class_name in enumerate(disease_service.class_names):
        parts = class_name.split("___", 1)
        crop = parts[0] if len(parts) > 0 else ""
        disease_name = parts[1] if len(parts) > 1 else class_name
        cn = disease_service.DISEASE_CN_NAMES.get(class_name, class_name)
        description = f"{crop} - {disease_name}"

        targets.append(TargetItem(
            id=idx,
            name=class_name,
            chinese_name=cn,
            description=description,
        ))

    return TargetListResponse(
        success=True,
        message="获取成功",
        data=targets,
    )


# =============================================================================
# MinIO 文件代理接口（病害模块专属）
# =============================================================================

@router.get("/files/{bucket}/{filename}", response_class=Response)
def get_file(bucket: str, filename: str):
    """
    MinIO 文件代理接口（本地文件回退）

    参数：
        bucket: Bucket 名称
        filename: 文件名

    返回：
        文件流
    """
    try:
        data = None
        content_type = "image/jpeg"
        if filename.endswith(".png"):
            content_type = "image/png"
        elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
            content_type = "image/jpeg"

        try:
            response = minio_service.client.get_object(bucket, filename)
            data = response.read()
            response.close()
            response.release_conn()
        except Exception:
            local_subdir = "results" if "result" in bucket.lower() else "uploads"
            local_path = os.path.join(settings.static_dir, local_subdir, filename)
            if os.path.exists(local_path):
                with open(local_path, "rb") as f:
                    data = f.read()
            else:
                raise FileNotFoundError(f"文件不存在: {local_path}")

        return Response(
            content=data,
            media_type=content_type,
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "Content-Length": str(len(data)),
            },
        )

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"{type(e).__name__}: {str(e)}")
