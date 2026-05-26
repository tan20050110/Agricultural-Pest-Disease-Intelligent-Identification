# -*- coding: utf-8 -*-
# =============================================================================
# FastAPI 应用入口 - 纯 API 模式（前端由 Nginx 托管）
# =============================================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.api.detection import router as detection_router
from app.api.disease import router as disease_router
from app.api.model import router as model_router
from app.api.auth import router as auth_router
from app.api.camera import router as camera_router
from app.api.qa import router as qa_router
from app.api.user import router as user_router
from app.utils.file_utils import ensure_directories

# 启动时确保必要的目录存在（上传目录、结果目录等）
ensure_directories()

# =============================================================================
# 创建 FastAPI 应用实例
# =============================================================================
app = FastAPI(
    title=settings.app_name,                                    # API 文档标题
    version=settings.app_version,                                # API 版本
    description="农业病虫害智能识别系统后端 API"                        # API 描述
)

# =============================================================================
# 配置 CORS 中间件
# =============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,                        # 允许的跨域来源
    allow_credentials=True,                                     # 允许携带凭证
    allow_methods=["*"],                                        # 允许所有 HTTP 方法
    allow_headers=["*"],                                        # 允许所有请求头
)

# =============================================================================
# 挂载静态文件目录
# =============================================================================
# 访问 URL: http://host:port/static/文件名
# 实际路径: settings.static_dir/文件名
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

# =============================================================================
# 注册 API 路由
# =============================================================================
# 所有虫害检测相关的 API 都会以 /api/detection 为前缀
app.include_router(detection_router, prefix="/api")
# 所有病害识别相关的 API 都会以 /api/disease 为前缀
app.include_router(disease_router, prefix="/api")
# 所有模型管理相关的 API 都会以 /api/model 为前缀
app.include_router(model_router, prefix="/api")
# 所有认证相关的 API 都会以 /api/auth 为前缀
app.include_router(auth_router, prefix="/api")
# 所有摄像头检测相关的 API 都会以 /api/camera 为前缀
app.include_router(camera_router, prefix="/api")
# 所有AI问答相关的 API 都会以 /api/qa 为前缀
app.include_router(qa_router, prefix="/api")
# 所有用户管理相关的 API 都会以 /api/user 为前缀
app.include_router(user_router, prefix="/api")


# =============================================================================
# 健康检查接口
# =============================================================================
@app.get("/health")
async def health_check():
    """
    健康检查接口

    功能：检查所有依赖服务的状态
    - PostgreSQL：数据库连接
    - MinIO：对象存储连接
    - Redis：缓存连接

    返回：
        dict: 包含各服务状态的字典
    """
    postgres_ok = False
    minio_ok = False
    redis_ok = False

    # 检查 PostgreSQL
    try:
        from app.models.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        postgres_ok = True
    except Exception:
        pass

    # 检查 Redis
    try:
        from app.services.redis_service import redis_service
        redis_ok = redis_service.ping()
    except Exception:
        pass

    # 检查 MinIO
    try:
        from app.services.minio_service import minio_service
        minio_service.client.list_buckets()
        minio_ok = True
    except Exception:
        pass

    # 计算整体状态
    all_ok = all([postgres_ok, minio_ok, redis_ok])
    status = "healthy" if all_ok else "degraded"

    return {
        "status": status,
        "services": {
            "postgres": "up" if postgres_ok else "down",
            "minio": "up" if minio_ok else "down",
            "redis": "up" if redis_ok else "down"
        }
    }


# =============================================================================
# 初始化默认管理员账号
# =============================================================================
def seed_default_admin():
    """如果管理员账号不存在则自动创建"""
    import hashlib, secrets
    from app.models.database import SessionLocal, User

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if not existing:
            salt = secrets.token_hex(16)
            pwd_hash = hashlib.sha256(("admin123" + salt).encode()).hexdigest()
            admin = User(
                username="admin",
                email="admin@example.com",
                password_hash=f"{salt}${pwd_hash}",
                nickname="管理员",
                role="admin",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            print("[INIT] 默认管理员账号已创建: admin / admin123")
        else:
            print("[INIT] 管理员账号已存在，跳过")
    except Exception as e:
        print(f"[INIT] 初始化管理员账号失败: {e}")
        db.rollback()
    finally:
        db.close()


# =============================================================================
# 应用启动事件
# =============================================================================
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    import logging
    logger = logging.getLogger(__name__)
    seed_default_admin()
    logger.info("模型将在首次检测时惰性加载")


# =============================================================================
# 应用启动入口
# =============================================================================
if __name__ == "__main__":
    import uvicorn                                               # ASGI 服务器

    uvicorn.run(
        "main:app",                                             # 应用模块路径
        host=settings.host,                                      # 监听地址
        port=settings.port,                                      # 监听端口
        reload=settings.debug,                                   # 开发模式启用热重载
        log_level="debug" if settings.debug else "info",         # 日志级别
        access_log=True                                          # 启用访问日志
    )