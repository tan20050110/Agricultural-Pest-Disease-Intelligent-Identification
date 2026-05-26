# =============================================================================
# 检测 API 路由模块
# =============================================================================
# 功能说明：
#   - 定义检测相关的 API 接口
#   - 处理图片上传、检测请求、结果返回
#   - 提供历史记录和目标类别查询接口
#   - 检测结果持久化存储到 PostgreSQL 数据库
#
# API 接口列表：
#   POST /api/detection/single    - 单图检测
#   GET  /api/detection/history   - 获取检测历史记录（从数据库）
#   GET  /api/detection/{id}      - 获取单个检测记录
#   DELETE /api/detection/{id}    - 删除检测记录
#   GET  /api/detection/targets/list - 获取可检测目标列表
#
# 使用示例：
#   # 前端调用
#   const formData = new FormData();
#   formData.append('file', imageFile);
#   formData.append('model_name', 'agri-pest-yolo11n');
#   const response = await fetch('/api/detection/single', {
#       method: 'POST',
#       body: formData
#   });
# =============================================================================

# 导入 os 模块，用于文件路径操作
import os

# 导入 FastAPI 相关组件
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Path, Response

# 导入检测服务
from app.services.detection_service import detection_service

# 导入 MinIO 服务
from app.services.minio_service import minio_service

# 导入文件工具函数
from app.utils.file_utils import save_upload_file, ensure_directories

# 导入应用配置
from app.config import settings

# 导入数据模型
from app.models.schemas import (
    SingleDetectionResponse,   # 单图检测响应模型
    HistoryResponse,          # 历史记录响应模型
    TargetListResponse,       # 目标列表响应模型
    TargetItem,               # 目标项数据模型
    HistoryItem,               # 历史记录项数据模型
    DetectionResult,           # 检测结果数据模型
    DetectionBox               # 检测框数据模型
)



# 创建 API 路由实例
# prefix: 所有路由的前缀，如 /api/detection
# tags: 用于 OpenAPI 文档分组
router = APIRouter(prefix="/detection", tags=["detection"])

# 在模块加载时确保必要的目录存在
ensure_directories()


# =============================================================================
# 单图检测接口
# =============================================================================

@router.post("/single", response_model=SingleDetectionResponse)
async def detect_single_image(
    file: UploadFile = File(...),      # 上传的图片文件（必填）
    model_name: str = Form("agri-pest-yolo11n"), # 使用的模型名称（可选）
    user_id: str = Form(None)          # 用户 ID（可选）
):
    """
    单图目标检测接口

    功能：
    - 接收用户上传的图片
    - 保存图片到服务器
    - 调用检测服务进行目标检测
    - 保存检测记录到数据库
    - 返回检测结果

    参数：
        file: 上传的图片文件，支持 jpg、png 等格式
        model_name: 使用的模型名称（可选，默认 agri-pest-yolo11n）
        user_id: 用户 ID（可选）

    返回：
        SingleDetectionResponse: 包含检测结果的响应

    响应示例：
        {
            "success": true,
            "message": "检测成功",
            "data": {
                "detection_id": "uuid-string",
                "image_url": "http://localhost:8000/static/uploads/xxx.jpg",
                "result_image_url": "http://localhost:8000/static/results/xxx.jpg",
                "boxes": [...],
                "total_objects": 5,
                "detection_time": 0.523,
                "model_name": "agri-pest-yolo11n",
                "created_at": "2024-12-01T14:30:00"
            }
        }
    """
    try:
        # 确保临时上传目录存在
        os.makedirs(settings.upload_dir, exist_ok=True)
        
        # 保存上传的文件到服务器
        # save_upload_file 是异步函数，使用 await 调用
        filename = await save_upload_file(file, settings.upload_dir)

        # 构建图片的完整路径
        image_path = os.path.join(settings.upload_dir, filename)

        # 调用检测服务进行单图检测（支持用户 ID）
        result = detection_service.detect_single_image(image_path, user_id, model_name, minio_service)

        # 检测完成后，删除临时上传的文件（节省空间）
        try:
            os.remove(image_path)
        except Exception:
            pass

        # 返回成功的响应
        return SingleDetectionResponse(
            success=True,                    # 请求成功
            message="检测成功",             # 提示信息
            data=result                      # 检测结果数据
        )

    except FileNotFoundError as e:
        # 模型文件未找到
        raise HTTPException(
            status_code=500,
            detail="模型文件未找到"
        )
    except Exception as e:
        # 如果检测过程中发生错误，抛出 500 错误
        raise HTTPException(
            status_code=500,                 # HTTP 状态码：服务器内部错误
            detail=f"检测失败: {str(e)}"    # 详细错误信息
        )


# =============================================================================
# 检测历史记录接口
# =============================================================================

@router.get("/history", response_model=HistoryResponse)
async def get_detection_history(
    page: int = 1,        # 页码（从 1 开始）
    page_size: int = 10,   # 每页记录数
    user_id: str = None    # 用户 ID（可选）
):
    """
    获取检测历史记录接口

    功能：
    - 从 PostgreSQL 数据库查询检测历史记录
    - 支持分页查询
    - 支持按用户 ID 筛选

    参数：
        page: 页码，默认 1
        page_size: 每页记录数，默认 10
        user_id: 用户 ID（可选）

    返回：
        HistoryResponse: 包含历史记录列表的响应

    响应示例：
        {
            "success": true,
            "message": "获取成功",
            "data": [
                {
                    "id": "uuid-string",
                    "image_url": "http://localhost:8000/static/uploads/xxx.jpg",
                    "result_image_url": "http://localhost:8000/static/results/xxx.jpg",
                    "total_objects": 3,
                    "created_at": "2024-12-01T14:30:00",
                    "model_name": "agri-pest-yolo11n"
                },
                ...
            ],
            "total": 15
        }
    """
    try:
        # 调用检测服务获取历史记录
        records = detection_service.get_detection_history(user_id=user_id, limit=page_size * page)

        # 计算分页
        start = (page - 1) * page_size
        end = start + page_size

        # 转换为 HistoryItem 列表
        history_items = []
        for record in records[start:end]:
            # 获取文件名（从 image_key 中提取）
            # 格式：uploads/xxx.jpg 或 results/xxx.jpg
            original_filename = os.path.basename(record.original_image_key) if record.original_image_key else ""
            result_filename = os.path.basename(record.result_image_key) if record.result_image_key else ""
            
            # 构建图片 URL：使用相对路径，由 nginx 代理
            if original_filename:
                image_url = f"/api/detection/files/agri-pest-original/{original_filename}" if minio_service.is_available else f"/static/uploads/{original_filename}"
            else:
                image_url = ""
            
            if result_filename:
                result_url = f"/api/detection/files/agri-pest-results/{result_filename}" if minio_service.is_available else f"/static/results/{result_filename}"
            else:
                result_url = ""
            
            # 从数据库查询检测到的目标名称
            detected_targets = []
            if hasattr(record, 'results') and record.results:
                detected_targets = list(set(
                    r.chinese_name or r.class_name for r in record.results 
                    if r.chinese_name or r.class_name
                ))

            history_items.append(HistoryItem(
                id=str(record.id),
                image_url=image_url,
                result_image_url=result_url,
                total_objects=record.total_objects or 0,
                created_at=record.created_at,
                model_name=record.model_name or "agri-pest-yolo11n",
                filename=original_filename or "detection.jpg",
                status=record.status or "completed",
                type=record.type or "single",
                time=record.created_at.strftime("%Y-%m-%d %H:%M") if record.created_at else "",
                count=1,
                detected_targets=detected_targets
            ))

        # 返回历史记录响应
        return HistoryResponse(
            success=True,                          # 请求成功
            message="获取成功",                     # 提示信息
            data=history_items,                    # 当前页的数据
            total=len(records)                     # 总记录数
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =============================================================================
# 获取单个检测记录接口
# =============================================================================

@router.get("/{detection_id}", response_model=SingleDetectionResponse)
async def get_detection_by_id(
    detection_id: str = Path(..., description="检测记录 ID")
):
    """
    获取单个检测记录接口

    功能：
    - 根据检测 ID 从数据库查询详细检测记录

    参数：
        detection_id: 检测记录 ID

    返回：
        SingleDetectionResponse: 包含检测结果的响应
    """
    try:
        # 调用检测服务获取检测记录
        record = detection_service.get_detection_by_id(detection_id)

        if not record:
            raise HTTPException(
                status_code=404,
                detail="检测记录不存在"
            )

        # 获取文件名
        original_filename = os.path.basename(record.original_image_key) if record.original_image_key else ""
        result_filename = os.path.basename(record.result_image_key) if record.result_image_key else ""
        
        # 构建图片 URL：使用相对路径，由 nginx 代理
        if original_filename:
            image_url = f"/api/detection/files/agri-pest-original/{original_filename}" if minio_service.is_available else f"/static/uploads/{original_filename}"
        else:
            image_url = ""
        
        if result_filename:
            result_url = f"/api/detection/files/agri-pest-results/{result_filename}" if minio_service.is_available else f"/static/results/{result_filename}"
        else:
            result_url = ""

        # 查询检测结果详情
        boxes = []
        if hasattr(record, 'results') and record.results:
            for result in record.results:
                boxes.append(DetectionBox(
                    x1=result.x1,
                    y1=result.y1,
                    x2=result.x2,
                    y2=result.y2,
                    confidence=result.confidence,
                    class_id=result.class_id,
                    class_name=result.class_name,
                    chinese_name=result.chinese_name,
                    treatment_advice=detection_service.get_treatment_advice(result.class_name)
                ))

        detection_result = DetectionResult(
            detection_id=str(record.id),
            image_url=image_url,
            result_image_url=result_url,
            boxes=boxes,
            total_objects=record.total_objects or 0,
            detection_time=record.detection_time or 0,
            model_name=record.model_name or "agri-pest-yolo11n",
            created_at=record.created_at
        )

        return SingleDetectionResponse(
            success=True,
            message="获取成功",
            data=detection_result
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =============================================================================
# 删除检测记录接口
# =============================================================================

@router.delete("/{detection_id}")
async def delete_detection(
    detection_id: str = Path(..., description="检测记录 ID")
):
    """
    删除检测记录接口

    功能：
    - 根据检测 ID 删除数据库中的检测记录及关联数据

    参数：
        detection_id: 检测记录 ID

    返回：
        dict: 删除结果
    """
    try:
        # 调用检测服务删除检测记录
        success = detection_service.delete_detection(detection_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail="检测记录不存在"
            )

        return {
            "success": True,
            "message": "删除成功"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =============================================================================
# 目标类别列表接口
# =============================================================================

@router.get("/targets/list", response_model=TargetListResponse)
async def get_target_list():
    """
    获取可检测目标类别列表接口

    功能：
    - 返回系统支持检测的所有目标类别

    返回：
        TargetListResponse: 包含目标类别列表的响应

    响应示例：
        {
            "success": true,
            "message": "获取成功",
            "data": [
                {
                    "id": 0,
                    "name": "rice_blast",
                    "chinese_name": "稻瘟病",
                    "description": "水稻常见真菌性病害"
                },
                ...
            ]
        }
    """
    targets = [
        TargetItem(id=0, name="rice_leaf_roller", chinese_name="稻纵卷叶螟", description="水稻主要害虫之一，幼虫卷叶为害"),
        TargetItem(id=1, name="rice_leaf_caterpillar", chinese_name="稻螟蛉", description="水稻重要害虫，以幼虫食叶为害"),
        TargetItem(id=2, name="paddy_stem_maggot", chinese_name="水稻蝇蛆", description="危害水稻茎秆的蝇类害虫"),
        TargetItem(id=3, name="asiatic_rice_borer", chinese_name="二化螟", description="水稻主要钻蛀性害虫"),
        TargetItem(id=4, name="yellow_rice_borer", chinese_name="三化螟", description="水稻重要钻蛀性害虫"),
        TargetItem(id=5, name="rice_gall_midge", chinese_name="稻瘿蚊", description="危害水稻形成虫瘿的害虫"),
        TargetItem(id=6, name="rice_stemfly", chinese_name="稻秆蝇", description="危害水稻茎秆的蝇类"),
        TargetItem(id=7, name="brown_plant_hopper", chinese_name="灰飞虱", description="水稻重要刺吸式害虫，传播病毒病"),
        TargetItem(id=8, name="white_backed_plant_hopper", chinese_name="白背飞虱", description="水稻重大迁飞性害虫"),
        TargetItem(id=9, name="small_brown_plant_hopper", chinese_name="褐飞虱", description="水稻最主要害虫之一，爆发性强"),
        TargetItem(id=10, name="rice_water_weevil", chinese_name="稻水象甲", description="水稻检疫性害虫"),
        TargetItem(id=11, name="rice_leafhopper", chinese_name="稻叶蝉", description="水稻叶蝉类刺吸式害虫"),
        TargetItem(id=12, name="grain_spreader_thrips", chinese_name="稻蓟马", description="危害水稻叶片的蓟马类害虫"),
        TargetItem(id=13, name="rice_shell_pest", chinese_name="稻苞虫", description="水稻食叶类害虫"),
        TargetItem(id=14, name="grub", chinese_name="蛴螬", description="地下主要害虫，危害多种作物根部"),
        TargetItem(id=15, name="mole_cricket", chinese_name="蝼蛄", description="地下害虫，危害作物根茎"),
        TargetItem(id=16, name="wireworm", chinese_name="金针虫", description="地下害虫，危害作物地下部分"),
        TargetItem(id=17, name="white_margined_moth", chinese_name="白边切夜蛾", description="危害作物幼苗的夜蛾类害虫"),
        TargetItem(id=18, name="black_cutworm", chinese_name="小地老虎", description="地下害虫，咬断作物幼苗"),
        TargetItem(id=19, name="large_cutworm", chinese_name="大地老虎", description="大型地下害虫"),
        TargetItem(id=20, name="yellow_cutworm", chinese_name="黄地老虎", description="地下害虫，多种作物受害"),
        TargetItem(id=21, name="red_spider", chinese_name="红蜘蛛", description="常见害螨，危害叶片导致黄化"),
        TargetItem(id=22, name="corn_borer", chinese_name="玉米螟", description="玉米主要钻蛀性害虫"),
        TargetItem(id=23, name="army_worm", chinese_name="黏虫", description="暴食性迁飞害虫，危害禾本科作物"),
        TargetItem(id=24, name="aphids", chinese_name="蚜虫", description="常见刺吸式害虫，传播病毒病"),
        TargetItem(id=25, name="potosia_brevitarsis", chinese_name="白星花金龟", description="危害多种果树和农作物的甲虫"),
        TargetItem(id=26, name="peach_borer", chinese_name="桃蛀螟", description="危害桃等果树的钻蛀性害虫"),
        TargetItem(id=27, name="english_grain_aphid", chinese_name="麦长管蚜", description="小麦主要蚜虫种类"),
        TargetItem(id=28, name="green_bug", chinese_name="麦二叉蚜", description="小麦重要蚜虫种类，传播病毒病"),
        TargetItem(id=29, name="bird_cherry_oat_aphid", chinese_name="燕麦蚜", description="危害燕麦等作物的蚜虫"),
        TargetItem(id=30, name="wheat_blossom_midge", chinese_name="麦红吸浆虫", description="小麦关键害虫，危害籽粒"),
        TargetItem(id=31, name="penthaleus_major", chinese_name="小麦红蜘蛛", description="小麦常见害螨"),
        TargetItem(id=32, name="longlegged_spider_mite", chinese_name="麦长腿蜘蛛", description="小麦害螨类"),
        TargetItem(id=33, name="wheat_phloeothrips", chinese_name="小麦皮蓟马", description="危害小麦的蓟马类害虫"),
        TargetItem(id=34, name="wheat_sawfly", chinese_name="麦叶蜂", description="小麦食叶类害虫"),
        TargetItem(id=35, name="cerodonta_denticornis", chinese_name="麦黑斑潜叶蝇", description="危害小麦叶片的潜叶蝇"),
        TargetItem(id=36, name="beet_fly", chinese_name="甜菜潜叶蝇", description="危害甜菜等作物的潜叶蝇"),
        TargetItem(id=37, name="flea_beetle", chinese_name="跳甲", description="危害多种蔬菜作物的甲虫"),
        TargetItem(id=38, name="cabbage_army_worm", chinese_name="甘蓝夜蛾", description="危害甘蓝等十字花科作物的夜蛾"),
        TargetItem(id=39, name="beet_army_worm", chinese_name="甜菜夜蛾", description="多食性害虫，危害多种作物"),
        TargetItem(id=40, name="beet_spot_flies", chinese_name="甜菜斑蝇", description="危害甜菜叶片的蝇类"),
        TargetItem(id=41, name="meadow_moth", chinese_name="草地螟", description="草原和农田重要害虫"),
        TargetItem(id=42, name="beet_weevil", chinese_name="甜菜象虫", description="甜菜主要害虫之一"),
        TargetItem(id=43, name="serica_orientalis", chinese_name="东方绢金龟", description="危害多种作物叶片的金龟子"),
        TargetItem(id=44, name="alfalfa_weevil", chinese_name="苜蓿叶象甲", description="危害苜蓿等豆科作物的象甲"),
        TargetItem(id=45, name="flax_budworm", chinese_name="苜蓿夜蛾", description="危害苜蓿的夜蛾类害虫"),
        TargetItem(id=46, name="alfalfa_plant_bug", chinese_name="苜蓿盲蝽", description="危害苜蓿的盲蝽类害虫"),
        TargetItem(id=47, name="tarnished_plant_bug", chinese_name="牧草盲蝽", description="危害牧草和多种作物的盲蝽"),
        TargetItem(id=48, name="locustoidea", chinese_name="蝗总科", description="重大农业害虫，暴食性"),
        TargetItem(id=49, name="lytta_polita", chinese_name="椿象", description="常见农业害虫"),
        TargetItem(id=50, name="legume_blister_beetle", chinese_name="豆芜菁", description="危害豆科作物的芫菁类"),
        TargetItem(id=51, name="blister_beetle", chinese_name="芜菁", description="芫菁类害虫"),
        TargetItem(id=52, name="theriophis_maculata", chinese_name="苜蓿蚜", description="危害苜蓿的蚜虫"),
        TargetItem(id=53, name="odontothrips_loti", chinese_name="牛角花齿蓟马", description="危害豆科作物的蓟马"),
        TargetItem(id=54, name="thrips", chinese_name="蓟马", description="常见小型害虫，锉吸式口器"),
        TargetItem(id=55, name="alfalfa_seed_chalcid", chinese_name="苜蓿广肩小蜂", description="危害苜蓿种子的小蜂类"),
        TargetItem(id=56, name="pieris_canidia", chinese_name="东方菜粉蝶", description="十字花科蔬菜常见害虫"),
        TargetItem(id=57, name="apolygus_lucorum", chinese_name="绿盲蝽", description="危害多种作物的盲蝽类害虫"),
        TargetItem(id=58, name="limacodidae", chinese_name="刺蛾科", description="多种果树和林木害虫"),
        TargetItem(id=59, name="viteus_vitifoliae", chinese_name="葡萄根瘤蚜", description="葡萄毁灭性检疫害虫"),
        TargetItem(id=60, name="colomerus_vitis", chinese_name="葡萄缺节瘿螨", description="危害葡萄叶片的瘿螨"),
        TargetItem(id=61, name="brevipalpus_lewisi", chinese_name="南天竹刘氏短须螨", description="危害多种果树的害螨"),
        TargetItem(id=62, name="oides_decempunctata", chinese_name="十星叶甲", description="葡萄等果树食叶害虫"),
        TargetItem(id=63, name="polyphagotarsonemus_latus", chinese_name="侧多食附线螨", description="多食性害螨，危害多种作物"),
        TargetItem(id=64, name="pseudococcus_comstocki", chinese_name="康氏粉蚧", description="危害果树的介壳虫类"),
        TargetItem(id=65, name="parathrene_regalis", chinese_name="葡萄透翅蛾", description="危害葡萄枝干的钻蛀性害虫"),
        TargetItem(id=66, name="ampelophaga", chinese_name="葡萄天蛾", description="危害葡萄叶片的天蛾类"),
        TargetItem(id=67, name="lycorma_delicatula", chinese_name="斑衣蜡蝉", description="危害多种果树和林木的蜡蝉"),
        TargetItem(id=68, name="xylotrechus", chinese_name="四带虎天牛", description="危害果树的天牛类害虫"),
        TargetItem(id=69, name="cicadella_viridis", chinese_name="大青叶蝉", description="危害多种作物的叶蝉类"),
        TargetItem(id=70, name="miridae", chinese_name="盲蝽科", description="盲蝽类害虫，危害多种作物"),
        TargetItem(id=71, name="trialeurodes_vaporariorum", chinese_name="温室粉虱", description="温室主要害虫之一"),
        TargetItem(id=72, name="erythroneura_apicalis", chinese_name="斑叶蝉", description="危害果树和作物的叶蝉类"),
        TargetItem(id=73, name="papilio_xuthus", chinese_name="柑橘凤蝶", description="柑橘类果树常见食叶害虫"),
        TargetItem(id=74, name="panonychus_citri", chinese_name="柑橘红蜘蛛", description="柑橘主要害螨之一"),
        TargetItem(id=75, name="phyllocoptes_oleiverus", chinese_name="柑橘锈螨", description="柑橘果实重要害螨"),
        TargetItem(id=76, name="icerya_purchasi", chinese_name="吹绵蚧", description="柑橘等果树介壳虫类"),
        TargetItem(id=77, name="unaspis_yanonensis", chinese_name="矢尖蚧", description="柑橘重要介壳虫"),
        TargetItem(id=78, name="ceroplastes_rubens", chinese_name="红蚧", description="危害果树的介壳虫"),
        TargetItem(id=79, name="chrysomphalus_aonidum", chinese_name="黑褐圆盾蚧", description="危害柑橘等果树的盾蚧"),
        TargetItem(id=80, name="parlatoria_zizyphus", chinese_name="黑点介壳虫", description="危害果树和观赏植物"),
        TargetItem(id=81, name="nipaecoccus_vastalor", chinese_name="堆蜡粉蚧", description="危害柑橘等果树的粉蚧"),
        TargetItem(id=82, name="aleurocanthus_spiniferus", chinese_name="黑刺粉虱", description="危害柑橘和茶树的粉虱"),
        TargetItem(id=83, name="bactrocera_minax", chinese_name="柑橘大实蝇", description="柑橘重大检疫性害虫"),
        TargetItem(id=84, name="dacus_dorsalis", chinese_name="柑桔小实蝇", description="柑橘类重要检疫害虫"),
        TargetItem(id=85, name="bactrocera_tsuneonis", chinese_name="蜜柑大实蝇", description="柑橘类检疫性害虫"),
        TargetItem(id=86, name="prodenia_litura", chinese_name="斜纹夜蛾", description="多食性暴食害虫"),
        TargetItem(id=87, name="adristyranus", chinese_name="枯叶夜蛾", description="危害果树的夜蛾类"),
        TargetItem(id=88, name="phyllocnistis_citrella", chinese_name="柑桔潜叶蛾", description="柑橘重要潜叶害虫"),
        TargetItem(id=89, name="toxoptera_citricidus", chinese_name="花椒蚜虫", description="危害柑橘和花椒的蚜虫"),
        TargetItem(id=90, name="toxoptera_aurantii", chinese_name="茶蚜", description="危害茶树和柑橘的蚜虫"),
        TargetItem(id=91, name="aphis_citricola", chinese_name="绣线菊蚜", description="危害多种果树的蚜虫"),
        TargetItem(id=92, name="scirtothrips_dorsalis", chinese_name="茶黄蓟马", description="危害茶树和多种作物的蓟马"),
        TargetItem(id=93, name="dasineura_sp", chinese_name="荔枝叶瘿蚊", description="危害荔枝叶片的瘿蚊类"),
        TargetItem(id=94, name="lawana_imitata", chinese_name="白翅蜡蝉", description="危害果树和林木的蜡蝉"),
        TargetItem(id=95, name="salurnis_marginella", chinese_name="褐缘蛾蜡蝉", description="危害多种植物的蜡蝉"),
        TargetItem(id=96, name="deporaus_marginatus", chinese_name="芒果切叶象甲", description="危害芒果叶片的象甲"),
        TargetItem(id=97, name="chlumetia_transversa", chinese_name="横线尾夜蛾", description="危害芒果的夜蛾类害虫"),
        TargetItem(id=98, name="mango_flat_beak_leafhopper", chinese_name="叶蝉", description="危害芒果的叶蝉类害虫"),
        TargetItem(id=99, name="rhytidodera_bowrinii", chinese_name="脊胸天牛", description="危害芒果枝干的天牛类害虫"),
        TargetItem(id=100, name="sternochetus_frigidus", chinese_name="芒果果肉象甲", description="危害芒果果实的象甲类害虫"),
        TargetItem(id=101, name="cicadellidae", chinese_name="叶蝉科", description="叶蝉科类害虫，危害多种作物"),
    ]

    # 返回目标列表响应
    return TargetListResponse(
        success=True,              # 请求成功
        message="获取成功",         # 提示信息
        data=targets              # 目标类别列表
    )


# =============================================================================
# MinIO 文件代理接口
# =============================================================================

@router.get("/files/{bucket}/{filename}", response_class=Response)
def get_file(bucket: str, filename: str):
    """
    MinIO 文件代理接口（本地文件回退）

    功能：
    - 优先从 MinIO 获取文件
    - MinIO 不可用时从本地 static 目录读取

    参数：
        bucket: MinIO Bucket 名称
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
        
        # 尝试从 MinIO 获取
        try:
            response = minio_service.client.get_object(bucket, filename)
            data = response.read()
            response.close()
            response.release_conn()
        except Exception:
            # MinIO 不可用，从本地 static 目录读取
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
                "Content-Length": str(len(data))
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"{type(e).__name__}: {str(e)}"
        )
