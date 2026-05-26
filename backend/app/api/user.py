# -*- coding: utf-8 -*-
# =============================================================================
# 用户信息 API 路由模块
# =============================================================================
import logging
from datetime import datetime

from fastapi import APIRouter, Form, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import func

from app.models.database import get_db, User, DetectionRecord
from app.services.auth_service import verify_password, hash_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["user"])


class UserInfoResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


class UpdateResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


@router.get("/info", response_model=UserInfoResponse)
async def get_user_info(user_id: str = None):
    """
    获取用户信息及统计数据
    
    参数：
        user_id: 用户 ID
    
    返回：
        用户信息和统计
    """
    try:
        db = next(get_db())
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "message": "用户不存在", "data": None}
        
        # 查询统计数据
        total_detections = db.query(func.count(DetectionRecord.id)).filter(
            DetectionRecord.user_id == user_id
        ).scalar() or 0
        
        total_targets = db.query(func.coalesce(func.sum(DetectionRecord.total_objects), 0)).filter(
            DetectionRecord.user_id == user_id
        ).scalar() or 0
        
        completed = db.query(func.count(DetectionRecord.id)).filter(
            DetectionRecord.user_id == user_id,
            DetectionRecord.status == "completed"
        ).scalar() or 0
        
        success_rate = round((completed / total_detections * 100), 1) if total_detections > 0 else 0
        
        # 计算使用天数
        first_record = db.query(func.min(DetectionRecord.created_at)).filter(
            DetectionRecord.user_id == user_id
        ).scalar()
        
        if first_record:
            days_used = (datetime.now() - first_record).days + 1
        else:
            days_used = 0
        
        return {
            "success": True,
            "message": "获取成功",
            "data": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "nickname": user.nickname or user.username,
                "role": user.role or "user",
                "avatar_url": user.avatar_url,
                "created_at": user.created_at.isoformat() if user.created_at else "",
                "stats": {
                    "total_detections": total_detections,
                    "total_targets": total_targets,
                    "success_rate": success_rate,
                    "days_used": days_used
                }
            }
        }
        
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update", response_model=UpdateResponse)
async def update_user_info(
    user_id: str = Form(...),
    nickname: str = Form(None),
    email: str = Form(None),
):
    """
    更新用户信息
    
    参数：
        user_id: 用户 ID
        nickname: 新昵称
        email: 新邮箱
    
    返回：
        更新结果
    """
    try:
        db = next(get_db())
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "message": "用户不存在", "data": None}
        
        if nickname:
            user.nickname = nickname
        if email:
            user.email = email
        
        user.updated_at = datetime.now()
        db.commit()
        db.refresh(user)
        
        return {
            "success": True,
            "message": "更新成功",
            "data": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "nickname": user.nickname or user.username,
                "role": user.role,
            }
        }
        
    except Exception as e:
        logger.error(f"更新用户信息失败: {e}")
        try:
            db.rollback()
        except:
            pass
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/change-password", response_model=UpdateResponse)
async def change_password(
    user_id: str = Form(...),
    old_password: str = Form(...),
    new_password: str = Form(...),
):
    """
    修改密码
    
    参数：
        user_id: 用户 ID
        old_password: 原密码
        new_password: 新密码
    
    返回：
        修改结果
    """
    try:
        if len(new_password) < 6:
            return {"success": False, "message": "新密码长度至少为6位", "data": None}
        
        db = next(get_db())
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "message": "用户不存在", "data": None}
        
        if not verify_password(old_password, user.password_hash):
            return {"success": False, "message": "原密码错误", "data": None}
        
        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.now()
        db.commit()
        
        return {"success": True, "message": "密码修改成功", "data": None}
        
    except Exception as e:
        logger.error(f"修改密码失败: {e}")
        try:
            db.rollback()
        except:
            pass
        raise HTTPException(status_code=500, detail=str(e))
