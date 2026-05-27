# =============================================================================
# 目标检测服务模块
# =============================================================================
# 功能说明：
#   - 封装 YOLO 目标检测模型的所有操作
#   - 提供单图检测、批量检测等接口
#   - 支持绘制检测框并保存结果图片
#   - 检测结果持久化存储到数据库
#
# YOLO 模型说明：
#   YOLO（You Only Look Once）是一种实时目标检测算法
#   本模块使用 Ultralytics 提供的 YOLO11 实现
#
# 检测流程：
#   1. 加载图片
#   2. 调用 YOLO 模型进行预测
#   3. 解析检测结果（框坐标、置信度、类别）
#   4. 绘制检测框到图片
#   5. 保存结果到数据库
#   6. 返回检测结果
#
# 使用示例：
#   from app.services.detection_service import detection_service
#
#   # 单图检测
#   result = detection_service.detect_single_image("/path/to/image.jpg", user_id="xxx")
#   print(f"检测到 {result.total_objects} 个目标")
# =============================================================================

import json
import os
import time
import uuid
import logging
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# 延迟导入重型依赖（YOLO、OpenCV），仅在需要时加载
YOLO = None
cv2 = None

def _ensure_ml_imports():
    """延迟导入机器学习和图像处理库"""
    global YOLO, cv2
    if YOLO is None:
        from ultralytics import YOLO as _YOLO
        YOLO = _YOLO
    if cv2 is None:
        import cv2 as _cv2
        cv2 = _cv2

from app.config import settings
from app.models.schemas import DetectionBox, DetectionResult
from app.models.database import DetectionRecord, DetectionResult as DBDetectionResult
from app.models.database import get_db
from app.services.minio_service import minio_service

logger = logging.getLogger(__name__)


class DetectionService:
    """
    目标检测服务类

    该类封装了 YOLO 目标检测的所有操作，包括：
    - 模型加载和初始化（智能版本管理）
    - 单图检测
    - 批量检测（预留）
    - 检测结果处理和可视化
    - 检测结果持久化存储
    """

    def __init__(self):
        """
        初始化检测服务（延迟加载模型）

        功能：
        - 初始化模型实例
        - 模型在首次使用时动态加载
        """
        self.model = None
        self.current_model_info = {
            "version": None,
            "object_name": None,
            "loaded_at": None,
            "metadata": None
        }
        self.local_model_info_path = Path(settings.yolo_model_path).parent / "model_info.json"
        self.class_names = {}
        # 初始化类别名称映射（不依赖重型库）
        self._init_class_names()
        # 延迟加载模型，在首次调用检测方法时加载

    def _save_local_model_info(self, model_info: dict):
        """
        保存本地模型信息到文件
        
        参数：
            model_info: 模型信息字典
        """
        try:
            info_path = Path(self.local_model_info_path)
            info_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(info_path, "w", encoding="utf-8") as f:
                json.dump(model_info, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.warning(f"保存本地模型信息失败: {str(e)}")

    def _load_local_model_info(self) -> Optional[dict]:
        """
        从文件加载本地模型信息
        
        返回：
            Optional[dict]: 模型信息字典
        """
        try:
            info_path = Path(self.local_model_info_path)
            if not info_path.exists():
                return None
                
            with open(info_path, "r", encoding="utf-8") as f:
                return json.load(f)
                
        except Exception as e:
            logger.warning(f"加载本地模型信息失败: {str(e)}")
            return None

    def _load_model_smart(self):
        """
        智能加载模型（版本检查与自动更新）

        功能：
        1. 检查本地模型是否存在
        2. 查询 MinIO 中的最新模型版本
        3. 如果本地没有或版本过旧，下载最新模型
        4. 加载模型并保存版本信息
        """
        _ensure_ml_imports()  # 确保重型依赖已导入
        # 检查是否有本地模型信息
        local_info = self._load_local_model_info()
        
        # 获取 MinIO 中的最新模型
        latest_model = minio_service.get_latest_model()
        
        need_download = False
        model_object_name = None
        
        # 情况 1：本地模型不存在
        if not os.path.exists(settings.yolo_model_path):
            logger.info("本地模型不存在，需要从 MinIO 下载")
            need_download = True
            
        # 情况 2：本地模型存在但没有信息
        elif not local_info:
            logger.info("本地模型存在但没有版本信息，检查 MinIO 最新版本")
            need_download = True
            
        # 情况 3：有本地信息，对比版本
        else:
            if latest_model:
                # 检查是否是同一个模型版本
                if local_info.get("object_name") != latest_model:
                    logger.info(f"发现新版本模型: {latest_model} (当前: {local_info.get('object_name', 'unknown')})")
                    need_download = True
                else:
                    logger.info(f"本地模型已是最新版本: {latest_model}")
        
        # 如果需要下载，从 MinIO 获取最新模型
        if need_download and latest_model:
            logger.info(f"从 MinIO 下载最新模型: {latest_model}")
            success = minio_service.download_model_file(latest_model, settings.yolo_model_path)
            if not success:
                # 如果下载失败但本地已有模型，继续使用本地模型
                if os.path.exists(settings.yolo_model_path):
                    logger.warning(f"模型下载失败，使用本地已有模型: {settings.yolo_model_path}")
                    model_object_name = local_info.get("object_name") if local_info else None
                else:
                    raise FileNotFoundError(f"模型下载失败且本地不存在: {latest_model}")
            else:
                model_object_name = latest_model
                logger.info(f"模型下载成功: {settings.yolo_model_path}")
        
        elif not latest_model:
            # 没有 MinIO 模型，检查本地是否存在
            if not os.path.exists(settings.yolo_model_path):
                raise FileNotFoundError(f"模型文件未找到: {settings.yolo_model_path}")
            model_object_name = local_info.get("object_name") if local_info else None
        
        else:
            # 本地已是最新
            model_object_name = local_info.get("object_name") if local_info else None
        
        # 加载 YOLO 模型
        self.model = YOLO(settings.yolo_model_path)
        
        # 获取并保存模型信息
        model_metadata = None
        if model_object_name:
            model_metadata = minio_service.get_model_metadata(model_object_name)
        
        # 更新当前模型信息
        self.current_model_info = {
            "version": model_metadata.get("version", "unknown") if model_metadata else "unknown",
            "object_name": model_object_name,
            "loaded_at": datetime.now().isoformat(),
            "metadata": model_metadata
        }
        
        # 保存到本地
        self._save_local_model_info(self.current_model_info)
        
        logger.info(f"模型加载成功: {settings.yolo_model_path} (版本: {self.current_model_info['version']})")
    
    def reload_model(self, model_object_name: Optional[str] = None) -> bool:
        """
        重新加载模型（可指定特定版本）
        
        参数：
            model_object_name: 可选的模型对象名称（MinIO 中的名称）
            
        返回：
            bool: 是否成功
        """
        try:
            if model_object_name:
                logger.info(f"加载指定模型: {model_object_name}")
                success = minio_service.download_model_file(model_object_name, settings.yolo_model_path)
                if not success:
                    logger.error(f"模型下载失败: {model_object_name}")
                    return False
            else:
                logger.info("重新加载最新模型")
            
            # 重新初始化
            self.model = None
            self._load_model_smart()
            return True
            
        except Exception as e:
            logger.error(f"重新加载模型失败: {str(e)}")
            return False

    def _init_class_names(self):
        """
        初始化类别名称映射

        功能：
        - 定义农业病虫害类别名称（102类）
        - 类别 ID 从 0 开始
        """
        self.class_names = {
            0: "rice_leaf_roller", 1: "rice_leaf_caterpillar", 2: "paddy_stem_maggot",
            3: "asiatic_rice_borer", 4: "yellow_rice_borer", 5: "rice_gall_midge",
            6: "rice_stemfly", 7: "brown_plant_hopper", 8: "white_backed_plant_hopper",
            9: "small_brown_plant_hopper", 10: "rice_water_weevil", 11: "rice_leafhopper",
            12: "grain_spreader_thrips", 13: "rice_shell_pest", 14: "grub",
            15: "mole_cricket", 16: "wireworm", 17: "white_margined_moth",
            18: "black_cutworm", 19: "large_cutworm", 20: "yellow_cutworm",
            21: "red_spider", 22: "corn_borer", 23: "army_worm",
            24: "aphids", 25: "potosia_brevitarsis", 26: "peach_borer",
            27: "english_grain_aphid", 28: "green_bug", 29: "bird_cherry_oat_aphid",
            30: "wheat_blossom_midge", 31: "penthaleus_major", 32: "longlegged_spider_mite",
            33: "wheat_phloeothrips", 34: "wheat_sawfly", 35: "cerodonta_denticornis",
            36: "beet_fly", 37: "flea_beetle", 38: "cabbage_army_worm",
            39: "beet_army_worm", 40: "beet_spot_flies", 41: "meadow_moth",
            42: "beet_weevil", 43: "serica_orientalis", 44: "alfalfa_weevil",
            45: "flax_budworm", 46: "alfalfa_plant_bug", 47: "tarnished_plant_bug",
            48: "locustoidea", 49: "lytta_polita", 50: "legume_blister_beetle",
            51: "blister_beetle", 52: "theriophis_maculata", 53: "odontothrips_loti",
            54: "thrips", 55: "alfalfa_seed_chalcid", 56: "pieris_canidia",
            57: "apolygus_lucorum", 58: "limacodidae", 59: "viteus_vitifoliae",
            60: "colomerus_vitis", 61: "brevipalpus_lewisi", 62: "oides_decempunctata",
            63: "polyphagotarsonemus_latus", 64: "pseudococcus_comstocki", 65: "parathrene_regalis",
            66: "ampelophaga", 67: "lycorma_delicatula", 68: "xylotrechus",
            69: "cicadella_viridis", 70: "miridae", 71: "trialeurodes_vaporariorum",
            72: "erythroneura_apicalis", 73: "papilio_xuthus", 74: "panonychus_citri",
            75: "phyllocoptes_oleiverus", 76: "icerya_purchasi", 77: "unaspis_yanonensis",
            78: "ceroplastes_rubens", 79: "chrysomphalus_aonidum", 80: "parlatoria_zizyphus",
            81: "nipaecoccus_vastalor", 82: "aleurocanthus_spiniferus", 83: "bactrocera_minax",
            84: "dacus_dorsalis", 85: "bactrocera_tsuneonis", 86: "prodenia_litura",
            87: "adristyranus", 88: "phyllocnistis_citrella", 89: "toxoptera_citricidus",
            90: "toxoptera_aurantii", 91: "aphis_citricola", 92: "scirtothrips_dorsalis",
            93: "dasineura_sp", 94: "lawana_imitata", 95: "salurnis_marginella",
            96: "deporaus_marginatus", 97: "chlumetia_transversa",
            98: "mango_flat_beak_leafhopper", 99: "rhytidodera_bowrinii",
            100: "sternochetus_frigidus", 101: "cicadellidae",
        }

    def get_class_chinese_name(self, class_name: str) -> str:
        """
        获取类别的中文名称

        参数：
            class_name: 类别英文名称

        返回：
            str: 类别中文名称
        """
        chinese_names = {
            "rice_leaf_roller": "稻纵卷叶螟", "rice_leaf_caterpillar": "稻螟蛉",
            "paddy_stem_maggot": "水稻蝇蛆", "asiatic_rice_borer": "二化螟",
            "yellow_rice_borer": "三化螟", "rice_gall_midge": "稻瘿蚊",
            "rice_stemfly": "稻秆蝇", "brown_plant_hopper": "灰飞虱",
            "white_backed_plant_hopper": "白背飞虱", "small_brown_plant_hopper": "褐飞虱",
            "rice_water_weevil": "稻水象甲", "rice_leafhopper": "稻叶蝉",
            "grain_spreader_thrips": "稻蓟马", "rice_shell_pest": "稻苞虫",
            "grub": "蛴螬", "mole_cricket": "蝼蛄", "wireworm": "金针虫",
            "white_margined_moth": "白边切夜蛾", "black_cutworm": "小地老虎",
            "large_cutworm": "大地老虎", "yellow_cutworm": "黄地老虎",
            "red_spider": "红蜘蛛", "corn_borer": "玉米螟", "army_worm": "黏虫",
            "aphids": "蚜虫", "potosia_brevitarsis": "白星花金龟",
            "peach_borer": "桃蛀螟", "english_grain_aphid": "麦长管蚜",
            "green_bug": "麦二叉蚜", "bird_cherry_oat_aphid": "燕麦蚜",
            "wheat_blossom_midge": "麦红吸浆虫", "penthaleus_major": "小麦红蜘蛛",
            "longlegged_spider_mite": "麦长腿蜘蛛", "wheat_phloeothrips": "小麦皮蓟马",
            "wheat_sawfly": "麦叶蜂", "cerodonta_denticornis": "麦黑斑潜叶蝇",
            "beet_fly": "甜菜潜叶蝇", "flea_beetle": "跳甲",
            "cabbage_army_worm": "甘蓝夜蛾", "beet_army_worm": "甜菜夜蛾",
            "beet_spot_flies": "甜菜斑蝇", "meadow_moth": "草地螟",
            "beet_weevil": "甜菜象虫", "serica_orientalis": "东方绢金龟",
            "alfalfa_weevil": "苜蓿叶象甲", "flax_budworm": "苜蓿夜蛾",
            "alfalfa_plant_bug": "苜蓿盲蝽", "tarnished_plant_bug": "牧草盲蝽",
            "locustoidea": "蝗总科", "lytta_polita": "椿象",
            "legume_blister_beetle": "豆芜菁", "blister_beetle": "芜菁",
            "theriophis_maculata": "苜蓿蚜", "odontothrips_loti": "牛角花齿蓟马",
            "thrips": "蓟马", "alfalfa_seed_chalcid": "苜蓿广肩小蜂",
            "pieris_canidia": "东方菜粉蝶", "apolygus_lucorum": "绿盲蝽",
            "limacodidae": "刺蛾科", "viteus_vitifoliae": "葡萄根瘤蚜",
            "colomerus_vitis": "葡萄缺节瘿螨", "brevipalpus_lewisi": "南天竹刘氏短须螨",
            "oides_decempunctata": "十星叶甲", "polyphagotarsonemus_latus": "侧多食附线螨",
            "pseudococcus_comstocki": "康氏粉蚧", "parathrene_regalis": "葡萄透翅蛾",
            "ampelophaga": "葡萄天蛾", "lycorma_delicatula": "斑衣蜡蝉",
            "xylotrechus": "四带虎天牛", "cicadella_viridis": "大青叶蝉",
            "miridae": "盲蝽科", "trialeurodes_vaporariorum": "温室粉虱",
            "erythroneura_apicalis": "斑叶蝉", "papilio_xuthus": "柑橘凤蝶",
            "panonychus_citri": "柑橘红蜘蛛", "phyllocoptes_oleiverus": "柑橘锈螨",
            "icerya_purchasi": "吹绵蚧", "unaspis_yanonensis": "矢尖蚧",
            "ceroplastes_rubens": "红蚧", "chrysomphalus_aonidum": "黑褐圆盾蚧",
            "parlatoria_zizyphus": "黑点介壳虫", "nipaecoccus_vastalor": "堆蜡粉蚧",
            "aleurocanthus_spiniferus": "黑刺粉虱", "bactrocera_minax": "柑橘大实蝇",
            "dacus_dorsalis": "柑桔小实蝇", "bactrocera_tsuneonis": "蜜柑大实蝇",
            "prodenia_litura": "斜纹夜蛾", "adristyranus": "枯叶夜蛾",
            "phyllocnistis_citrella": "柑桔潜叶蛾", "toxoptera_citricidus": "花椒蚜虫",
            "toxoptera_aurantii": "茶蚜", "aphis_citricola": "绣线菊蚜",
            "scirtothrips_dorsalis": "茶黄蓟马", "dasineura_sp": "荔枝叶瘿蚊",
            "lawana_imitata": "白翅蜡蝉", "salurnis_marginella": "褐缘蛾蜡蝉",
            "deporaus_marginatus": "芒果切叶象甲", "chlumetia_transversa": "横线尾夜蛾",
            "mango_flat_beak_leafhopper": "叶蝉", "rhytidodera_bowrinii": "脊胸天牛",
            "sternochetus_frigidus": "芒果果肉象甲", "cicadellidae": "叶蝉科",
        }
        return chinese_names.get(class_name, class_name)

    def get_treatment_advice(self, class_name: str) -> str:
        """
        获取害虫防治建议

        参数：
            class_name: 害虫英文名称

        返回：
            str: 防治建议文本
        """
        default_advice = "请结合当地实际情况，采取综合防治措施（农业防治、生物防治、物理防治、化学防治相结合）。建议咨询当地农技部门获取更精准的防治方案。"

        treatment_advice = {
            # ========== 水稻害虫 (0-13) ==========
            "rice_leaf_roller": (
                "【稻纵卷叶螟】水稻重要迁飞性害虫，幼虫缀叶成苞潜食叶肉。防治方法："
                "1. 农业防治：选用抗虫品种，合理施肥避免贪青；"
                "2. 生物防治：释放赤眼蜂（每亩1-2万头），使用Bt制剂（苏云金杆菌）喷雾；"
                "3. 化学防治：在幼虫1-2龄高峰期施药，可选用氯虫苯甲酰胺、甲维盐、阿维菌素、茚虫威等。"
                "防治适期为卵孵盛期至低龄幼虫期。"
            ),
            "rice_leaf_caterpillar": (
                "【稻螟蛉】幼虫取食叶片，造成白条斑或孔洞。防治方法："
                "1. 农业防治：清除田边杂草，减少虫源；"
                "2. 物理防治：灯光诱杀成虫（黑光灯或频振式杀虫灯）；"
                "3. 化学防治：在幼虫低龄期施药，可选用高效氯氟氰菊酯、毒死蜱、阿维菌素等。"
                "注意保护寄生蜂等天敌。"
            ),
            "paddy_stem_maggot": (
                "【水稻蝇蛆】幼虫蛀入稻茎为害，造成枯心苗。防治方法："
                "1. 农业防治：清除越冬杂草，整地时深耕灭蛹；"
                "2. 化学防治：秧田期和本田返青期是关键防治时期，可选用毒死蜱、辛硫磷颗粒剂撒施，或喷施阿维菌素、高效氯氰菊酯。"
                "在水稻移栽后7-10天重点防治。"
            ),
            "asiatic_rice_borer": (
                "【二化螟】水稻主要钻蛀性害虫，造成枯鞘、枯心、白穗。防治方法："
                "1. 农业防治：齐泥割稻，春季灌水灭蛹（淹没稻桩7-10天）；"
                "2. 物理防治：性诱剂诱杀雄蛾（每亩1个诱捕器），灯光诱杀；"
                "3. 生物防治：释放赤眼蜂，使用Bt制剂；"
                "4. 化学防治：在卵孵高峰期施药，可选用氯虫苯甲酰胺、杀虫双、杀虫单、阿维菌素等。"
                "重点防治越冬代和第一代。"
            ),
            "yellow_rice_borer": (
                "【三化螟】单食性水稻害虫，幼虫蛀茎造成枯心和白穗。防治方法："
                "1. 农业防治：调整播种期避开螟害，灌水灭蛹；"
                "2. 物理防治：灯光诱杀成虫（黑光灯）；"
                "3. 化学防治：在蚁螟盛孵期施药，可选用氯虫苯甲酰胺、杀虫双、毒死蜱等。"
                "防治关键期为卵孵高峰期，用药需掌握\"早、准、狠\"原则。"
            ),
            "rice_gall_midge": (
                "【稻瘿蚊】幼虫侵入生长点为害，形成葱管（标葱）。防治方法："
                "1. 农业防治：铲除田间和李氏禾等越冬寄主，合理轮作；"
                "2. 化学防治：秧田期用药（送嫁药）是关键，可选用毒死蜱、吡虫啉颗粒剂拌种或撒施。"
                "标葱率超过3-5%时需及时防治。"
            ),
            "rice_stemfly": (
                "【稻秆蝇】幼虫蛀入心叶或幼穗为害。防治方法："
                "1. 农业防治：清除田边游草等寄主杂草；"
                "2. 化学防治：成虫盛发期或卵孵盛期施药，可选用毒死蜱、高效氯氰菊酯、阿维菌素等喷雾。"
            ),
            "brown_plant_hopper": (
                "【灰飞虱】刺吸式害虫，除直接为害外还传播水稻条纹叶枯病等病毒。防治方法："
                "1. 农业防治：清除田边杂草（病毒中间寄主），合理密植；"
                "2. 化学防治：在若虫高峰期施药，可选用吡虫啉、噻虫嗪、烯啶虫胺、吡蚜酮等。"
                "注意灰飞虱传毒能力极强，以\"治虫防病\"为原则，苗期重点防治。"
            ),
            "white_backed_plant_hopper": (
                "【白背飞虱】迁飞性害虫，刺吸稻株汁液造成虱烧。防治方法："
                "1. 农业防治：选用抗虫品种，合理施肥避免贪青；"
                "2. 化学防治：在若虫高峰期施药，可选用吡虫啉、噻嗪酮、醚菊酯、烯啶虫胺等。"
                "防治指标：孕穗期百丛虫量1000-1500头。"
            ),
            "small_brown_plant_hopper": (
                "【褐飞虱】水稻最危险害虫之一，可造成大面积虱烧枯死。防治方法："
                "1. 农业防治：选用抗虫品种（含Bph抗性基因），合理水肥管理；"
                "2. 化学防治：在若虫高峰期施药，可选用吡蚜酮、烯啶虫胺、氟啶虫胺腈、三氟苯嘧啶等。"
                "防治指标：分蘖期百丛1000头，孕穗期百丛500-800头。注意药剂轮换使用延缓抗性。"
            ),
            "rice_water_weevil": (
                "【稻水象甲】检疫性害虫，成虫取食叶片，幼虫蛀食稻根。防治方法："
                "1. 检疫防控：严禁从疫区调运秧苗和稻草；"
                "2. 农业防治：水旱轮作，清除田边杂草；"
                "3. 化学防治：成虫盛发期喷施氯虫苯甲酰胺、高效氯氟氰菊酯等；幼虫期用毒死蜱颗粒剂撒施。"
            ),
            "rice_leafhopper": (
                "【稻叶蝉】刺吸式害虫，传播水稻矮缩病等病毒。防治方法："
                "1. 农业防治：清除田边杂草，合理密植；"
                "2. 物理防治：灯光诱杀（黑光灯）；"
                "3. 化学防治：若虫高峰期施药，可选用吡虫啉、噻虫嗪、异丙威、仲丁威等。"
            ),
            "grain_spreader_thrips": (
                "【稻蓟马】锉吸式害虫，为害水稻心叶和幼穗。防治方法："
                "1. 农业防治：清除田边杂草减少虫源；"
                "2. 化学防治：秧田期和分蘖期重点防治，可选用吡虫啉、噻虫嗪、阿维菌素、乙基多杀菌素等喷雾。"
                "防治适期为卷叶株率达5%以上时。"
            ),
            "rice_shell_pest": (
                "【稻苞虫】幼虫吐丝缀叶成苞，在苞内取食。防治方法："
                "1. 农业防治：清除田边杂草，人工摘除虫苞；"
                "2. 生物防治：保护寄生蜂（稻苞虫绒茧蜂等）天敌；"
                "3. 化学防治：幼虫低龄期施药，可选用高效氯氟氰菊酯、阿维菌素、Bt制剂等。"
            ),

            # ========== 地下害虫 (14-20) ==========
            "grub": (
                "【蛴螬】金龟子幼虫，咬食作物根部和地下茎。防治方法："
                "1. 农业防治：深翻土壤，施用腐熟有机肥；"
                "2. 物理防治：灯光诱杀成虫（金龟子），人工捡拾幼虫；"
                "3. 化学防治：播种前用辛硫磷颗粒剂土壤处理，或用毒死蜱、辛硫磷灌根。"
                "成虫盛发期喷药防治金龟子可有效减少下一代蛴螬数量。"
            ),
            "mole_cricket": (
                "【蝼蛄】地下害虫，咬食种子和幼苗根部，挖掘隧道。防治方法："
                "1. 农业防治：深翻土壤破坏蝼蛄栖息环境；"
                "2. 物理防治：灯光诱杀成虫，马粪诱杀；"
                "3. 化学防治：播种前用辛硫磷拌种，或制作毒饵（麦麸+敌百虫）撒施田间。"
            ),
            "wireworm": (
                "【金针虫】叩头虫幼虫，钻蛀作物根茎和种子。防治方法："
                "1. 农业防治：深翻土壤，合理轮作（水稻-旱作轮作效果好）；"
                "2. 化学防治：播种前用辛硫磷、毒死蜱颗粒剂进行土壤处理，或种子包衣（噻虫嗪、吡虫啉等）。"
            ),
            "white_margined_moth": (
                "【白边切夜蛾】幼虫夜间出土咬断幼苗根茎。防治方法："
                "1. 农业防治：清除田间杂草减少虫源；"
                "2. 物理防治：糖醋液诱杀成虫；"
                "3. 化学防治：傍晚喷施高效氯氟氰菊酯、毒死蜱等药剂于幼苗基部。"
            ),
            "black_cutworm": (
                "【小地老虎】重要地下害虫，幼虫咬断幼苗造成缺苗断垄。防治方法："
                "1. 农业防治：清除田间杂草（成虫产卵场所）；"
                "2. 物理防治：糖醋液或灯光诱杀成虫；"
                "3. 化学防治：幼虫1-2龄期喷施高效氯氟氰菊酯、溴氰菊酯等，高龄幼虫用毒饵（鲜草+敌百虫）诱杀。"
                "防治适期为幼虫3龄之前。"
            ),
            "large_cutworm": (
                "【大地老虎】幼虫咬食作物根茎。防治方法同小地老虎："
                "清除杂草、灯光诱杀、低龄期喷药防治，高龄幼虫用毒饵诱杀。"
                "建议结合冬耕消灭越冬幼虫。"
            ),
            "yellow_cutworm": (
                "【黄地老虎】幼虫为害多种旱作物。防治方法："
                "1. 农业防治：清除杂草、秋翻冬灌降低虫口密度；"
                "2. 化学防治：播种前土壤处理（辛硫磷颗粒剂），出苗后低龄幼虫期喷施高效氯氟氰菊酯等药剂。"
            ),

            # ========== 杂粮害虫 (21-26) ==========
            "red_spider": (
                "【红蜘蛛（叶螨）】刺吸式害虫，危害叶片造成黄白斑点甚至枯焦。防治方法："
                "1. 农业防治：清除杂草和枯枝落叶，高温干旱季节适当喷水增加湿度；"
                "2. 生物防治：释放捕食螨（胡瓜钝绥螨等）；"
                "3. 化学防治：可选用阿维菌素、哒螨灵、噻螨酮、联苯肼酯、乙螨唑等，注意轮换用药避免产生抗性。"
                "高温干旱天气利于发生，需加强监测。"
            ),
            "corn_borer": (
                "【玉米螟】玉米主要钻蛀性害虫，幼虫蛀入茎秆和果穗。防治方法："
                "1. 农业防治：处理玉米秸秆（粉碎还田或集中销毁越冬幼虫），选用抗虫品种；"
                "2. 生物防治：释放赤眼蜂（每亩1-2万头），使用Bt颗粒剂灌心；"
                "3. 化学防治：在大喇叭口期施药灌心，可选用氯虫苯甲酰胺、高效氯氟氰菊酯等。"
                "防治关键时期为大喇叭口期。"
            ),
            "army_worm": (
                "【黏虫】暴食性迁飞害虫，大发生时可将作物叶片吃光。防治方法："
                "1. 农业防治：清除田间杂草，合理密植；"
                "2. 物理防治：糖醋液诱杀成虫，杨树枝把诱蛾，灯光诱杀；"
                "3. 化学防治：幼虫3龄前施药效果最佳，可选用高效氯氟氰菊酯、甲维盐、氯虫苯甲酰胺等。"
                "注意预测预报，在低龄幼虫期集中防治。"
            ),
            "aphids": (
                "【蚜虫】常见刺吸式害虫，造成叶片卷曲变形、排泄蜜露引发煤污病，还传播多种病毒病。防治方法："
                "1. 农业防治：清除田间杂草；"
                "2. 物理防治：银灰色地膜驱避，黄色粘虫板诱杀（每亩20-30块）；"
                "3. 生物防治：保护瓢虫、草蛉、食蚜蝇等天敌，释放蚜茧蜂；"
                "4. 化学防治：可用吡虫啉、啶虫脒、氟啶虫胺腈、噻虫嗪等喷雾。"
            ),
            "potosia_brevitarsis": (
                "【白星花金龟】成虫取食多种农作物的花、果实和嫩叶。防治方法："
                "1. 农业防治：施用腐熟有机肥减少幼虫滋生，人工捕杀成虫；"
                "2. 物理防治：糖醋液诱杀成虫（红糖:醋:酒:水=3:3:1:10）；"
                "3. 化学防治：成虫盛发期喷施高效氯氟氰菊酯等药剂。"
            ),
            "peach_borer": (
                "【桃蛀螟】幼虫蛀食桃、玉米、向日葵等多种作物的果实和茎秆。防治方法："
                "1. 农业防治：清除越冬寄主，果实套袋，及时处理虫果；"
                "2. 物理防治：灯光诱杀成虫，性诱剂诱杀；"
                "3. 化学防治：卵孵盛期施药，可选用氯虫苯甲酰胺、高效氯氟氰菊酯、甲维盐等。"
            ),

            # ========== 小麦害虫 (27-36) ==========
            "english_grain_aphid": (
                "【麦长管蚜】小麦重要刺吸式害虫，穗期为害最重，还传播大麦黄矮病毒。防治方法："
                "1. 农业防治：适期播种，合理施肥，清除田间杂草；"
                "2. 生物防治：保护瓢虫、草蛉、食蚜蝇等天敌；"
                "3. 化学防治：穗期百穗蚜量达500头时施药，可选用吡虫啉、啶虫脒、高效氯氟氰菊酯等。"
            ),
            "green_bug": (
                "【麦二叉蚜】小麦重要害虫，传播大麦黄矮病毒能力极强。防治方法："
                "1. 农业防治：适期晚播减少秋苗蚜量；"
                "2. 化学防治：苗期和返青拔节期重点防治，药剂同麦长管蚜。"
                "秋苗期重点防治可有效降低病毒病发生。"
            ),
            "bird_cherry_oat_aphid": (
                "【燕麦蚜（禾谷缢管蚜）】为害小麦、燕麦等禾本科作物。防治方法："
                "同麦长管蚜，在发生高峰期选用吡虫啉、啶虫脒、高效氯氟氰菊酯等药剂喷雾防治。"
            ),
            "wheat_blossom_midge": (
                "【麦红吸浆虫】幼虫吸食麦粒浆液造成瘪粒减产。防治方法："
                "1. 农业防治：选用抗虫品种，深翻土壤灭茧；"
                "2. 化学防治：小麦抽穗期（成虫出土盛期）喷施毒死蜱、高效氯氟氰菊酯等，或用毒死蜱颗粒剂土壤处理。"
                "防治适期为小麦抽穗至扬花期。"
            ),
            "penthaleus_major": (
                "【小麦红蜘蛛（麦圆叶爪螨）】刺吸叶片汁液，造成黄白色斑点。防治方法："
                "1. 农业防治：轮作倒茬，灌水灭虫，清除田间杂草；"
                "2. 化学防治：春季每尺单行螨量达200头时施药，可选用阿维菌素、哒螨灵、联苯菊酯等。"
            ),
            "longlegged_spider_mite": (
                "【麦长腿蜘蛛】干旱型叶螨，喜干燥温暖环境。防治方法："
                "1. 农业防治：适时灌溉增加田间湿度；"
                "2. 化学防治：同小麦红蜘蛛，注意与其他叶螨交替用药。"
            ),
            "wheat_phloeothrips": (
                "【小麦皮蓟马】锉吸式害虫，为害小麦花器和籽粒。防治方法："
                "1. 农业防治：深翻土壤灭虫，清除田间杂草；"
                "2. 化学防治：小麦抽穗期（成虫盛发期）喷施吡虫啉、阿维菌素、乙基多杀菌素等。"
            ),
            "wheat_sawfly": (
                "【麦叶蜂】幼虫取食小麦叶片造成缺刻。防治方法："
                "1. 农业防治：深翻土壤破坏蛹室；"
                "2. 化学防治：幼虫3龄前（体长小于10mm）施药，可选用高效氯氟氰菊酯、毒死蜱等。"
            ),
            "cerodonta_denticornis": (
                "【麦黑斑潜叶蝇】幼虫潜食叶肉形成隧道。防治方法："
                "1. 农业防治：清除田边杂草，深翻灭蛹；"
                "2. 化学防治：成虫盛发期或幼虫初孵期施药，可选用阿维菌素、灭蝇胺、高效氯氰菊酯等。"
            ),

            # ========== 甜菜害虫 (37-43) ==========
            "beet_fly": (
                "【甜菜潜叶蝇】幼虫潜食甜菜叶片形成隧道。防治方法："
                "1. 农业防治：清除田间杂草和残株，深翻灭蛹；"
                "2. 化学防治：成虫盛发期或产卵盛期施药，可选用阿维菌素、灭蝇胺、高效氯氰菊酯等喷雾。"
            ),
            "flea_beetle": (
                "【跳甲】成虫取食叶片形成小孔，幼虫蛀食根部。防治方法："
                "1. 农业防治：清除田间杂草，轮作倒茬，适当调整播种期；"
                "2. 化学防治：苗期重点防治，可选用高效氯氟氰菊酯、啶虫脒、噻虫嗪等。"
                "跳甲成虫跳跃能力强，施药时建议从田边向内包围式喷洒。"
            ),
            "cabbage_army_worm": (
                "【甘蓝夜蛾】暴食性害虫，幼虫取食叶片造成孔洞。防治方法："
                "1. 农业防治：清除田间杂草和残株；"
                "2. 物理防治：灯光诱杀成虫，糖醋液诱杀；"
                "3. 生物防治：使用Bt制剂（苏云金杆菌）或核型多角体病毒；"
                "4. 化学防治：幼虫3龄前施药，可选用高效氯氟氰菊酯、甲维盐、氯虫苯甲酰胺等。"
            ),
            "beet_army_worm": (
                "【甜菜夜蛾】世界性重要害虫，幼虫暴食性强且抗药性严重。防治方法："
                "1. 农业防治：清除杂草和残株，深翻灭蛹；"
                "2. 物理防治：性诱剂诱杀雄蛾，灯光诱杀；"
                "3. 生物防治：使用Bt制剂，保护天敌（寄生蜂等）；"
                "4. 化学防治：幼虫低龄期施药，注意轮换用药，可选用甲维盐、茚虫威、氯虫苯甲酰胺、虫螨腈等。"
                "甜菜夜蛾抗药性强，切勿连续使用同一类药剂。"
            ),
            "beet_spot_flies": (
                "【甜菜斑蝇（甜菜泉蝇）】幼虫潜叶为害。防治方法："
                "1. 农业防治：清除田间残株和杂草，深翻灭蛹；"
                "2. 化学防治：成虫盛发期喷施高效氯氰菊酯、阿维菌素等药剂。"
            ),
            "meadow_moth": (
                "【草地螟】间歇性暴发害虫，幼虫取食叶片。防治方法："
                "1. 农业防治：清除田间杂草（成虫产卵场所）；"
                "2. 物理防治：灯光诱杀成虫；"
                "3. 化学防治：幼虫3龄前施药效果最好，可选用高效氯氟氰菊酯、甲维盐等。"
                "注意监测成虫迁入量，必要时在幼虫低龄期进行统一防治。"
            ),
            "beet_weevil": (
                "【甜菜象虫（甜菜象甲）】成虫取食幼苗，幼虫蛀食根部。防治方法："
                "1. 农业防治：轮作倒茬，适时早播；"
                "2. 化学防治：播种前用噻虫嗪等药剂种子包衣，苗期喷施高效氯氟氰菊酯等。"
            ),

            # ========== 苜蓿/牧草害虫 (43-55) ==========
            "serica_orientalis": (
                "【东方绢金龟】成虫取食植物叶片和花。防治方法："
                "1. 农业防治：施用腐熟有机肥减少幼虫滋生；"
                "2. 物理防治：灯光诱杀成虫；"
                "3. 化学防治：成虫盛发期喷施高效氯氟氰菊酯等药剂。"
            ),
            "alfalfa_weevil": (
                "【苜蓿叶象甲】幼虫和成虫均取食苜蓿叶片。防治方法："
                "1. 农业防治：早春刈割减少虫口，合理轮作；"
                "2. 化学防治：幼虫低龄期施药，可选用高效氯氟氰菊酯、毒死蜱等。"
            ),
            "flax_budworm": (
                "【苜蓿夜蛾】幼虫取食苜蓿叶片和花蕾。防治方法："
                "1. 农业防治：适时刈割（幼虫大量发生时）；"
                "2. 生物防治：使用Bt制剂；"
                "3. 化学防治：幼虫低龄期施药，可选用高效氯氟氰菊酯、甲维盐等。"
            ),
            "alfalfa_plant_bug": (
                "【苜蓿盲蝽】刺吸式害虫，为害苜蓿嫩茎和花蕾。防治方法："
                "1. 农业防治：清除田边杂草（越冬场所）；"
                "2. 化学防治：若虫盛发期施药，可选用高效氯氟氰菊酯、吡虫啉等。"
            ),
            "tarnished_plant_bug": (
                "【牧草盲蝽】刺吸式害虫，寄主广泛。防治方法同苜蓿盲蝽："
                "清除田边杂草，若虫期喷施高效氯氟氰菊酯、吡虫啉等药剂。"
            ),
            "locustoidea": (
                "【蝗总科（蝗虫）】农业重大害虫，暴食性，可形成蝗灾。防治方法："
                "1. 生态控制：保护天敌（鸟类、蛙类、寄生蜂等），改造蝗区生态环境；"
                "2. 生物防治：使用蝗虫微孢子虫、绿僵菌等生物制剂；"
                "3. 化学防治：在蝗蝻（若虫）3龄前集中防治效果最佳，可选用马拉硫磷、高效氯氰菊酯、氟虫脲等。"
                "对于飞蝗，需建立监测预警体系，\"预防为主，综合治理\"。"
            ),
            "lytta_polita": (
                "【椿象（蝽象）】刺吸式害虫，造成果实畸形、叶片萎蔫。防治方法："
                "1. 农业防治：清除杂草，合理密植；"
                "2. 化学防治：若虫低龄期（聚集为害期）施药效果最好，可选用高效氯氟氰菊酯、啶虫脒、吡虫啉等。"
            ),
            "legume_blister_beetle": (
                "【豆芜菁】成虫取食豆科植物叶片和花。防治方法："
                "1. 农业防治：深翻灭蛹，合理轮作；"
                "2. 化学防治：成虫盛发期喷施高效氯氟氰菊酯等药剂。"
                "注意：芜菁成虫体液含斑蝥素，对人体皮肤有刺激作用，人工捕杀需戴手套。"
            ),
            "blister_beetle": (
                "【芜菁】成虫取食多种作物叶片。防治方法："
                "成虫盛发期喷施高效氯氟氰菊酯、毒死蜱等药剂。人工捕杀需戴手套防斑蝥素刺激皮肤。"
            ),
            "theriophis_maculata": (
                "【苜蓿蚜（苜蓿斑翅蚜）】刺吸式害虫，为害苜蓿嫩茎和叶片。防治方法："
                "保护瓢虫等天敌，严重时喷施吡虫啉、啶虫脒等药剂。"
            ),
            "odontothrips_loti": (
                "【牛角花齿蓟马】刺吸式害虫，为害苜蓿和牧草。防治方法："
                "1. 农业防治：清除田间杂草；"
                "2. 化学防治：若虫盛发期喷施吡虫啉、阿维菌素、乙基多杀菌素等。"
            ),
            "thrips": (
                "【蓟马】锉吸式害虫，为害多种作物的嫩叶、花和幼果。防治方法："
                "1. 农业防治：清除田间杂草，合理灌溉；"
                "2. 物理防治：蓝色粘虫板诱杀（每亩20-30块）；"
                "3. 化学防治：若虫盛发期喷施吡虫啉、噻虫嗪、乙基多杀菌素、阿维菌素等。"
                "蓟马世代短、繁殖快，需连续防治2-3次，间隔7-10天。"
            ),
            "alfalfa_seed_chalcid": (
                "【苜蓿广肩小蜂】幼虫蛀食苜蓿种子。防治方法："
                "1. 农业防治：适时早收减少虫害损失；"
                "2. 化学防治：成虫盛发期喷施高效氯氟氰菊酯等药剂。"
            ),

            # ========== 蔬菜/十字花科害虫 (56-57) ==========
            "pieris_canidia": (
                "【东方菜粉蝶】幼虫取食十字花科蔬菜叶片。防治方法："
                "1. 农业防治：清除田间残株，人工摘除卵块和幼虫；"
                "2. 生物防治：使用Bt制剂（苏云金杆菌），保护寄生蜂天敌；"
                "3. 化学防治：幼虫低龄期施药，可选用高效氯氟氰菊酯、阿维菌素等。"
            ),
            "apolygus_lucorum": (
                "【绿盲蝽】刺吸式害虫，为害棉花、枣树、葡萄等多种作物。防治方法："
                "1. 农业防治：清除田间杂草（越冬寄主）；"
                "2. 化学防治：若虫盛发期施药，可选用高效氯氟氰菊酯、吡虫啉、氟啶虫胺腈等。"
                "越冬代成虫防治是关键。"
            ),

            # ========== 林木害虫 (58) ==========
            "limacodidae": (
                "【刺蛾科（洋辣子）】幼虫体表有毒刺，取食叶片，接触人体皮肤引起剧痛。防治方法："
                "1. 农业防治：冬季摘除树干上的虫茧（硬壳茧）；"
                "2. 生物防治：保护刺蛾紫姬蜂等天敌，使用Bt制剂；"
                "3. 化学防治：幼虫低龄期喷施高效氯氟氰菊酯、毒死蜱等。"
                "注意：人工操作需穿戴防护衣物，避免皮肤接触幼虫毒刺。"
            ),

            # ========== 葡萄害虫 (59-68) ==========
            "viteus_vitifoliae": (
                "【葡萄根瘤蚜】毁灭性检疫害虫，为害葡萄根部和叶片。防治方法："
                "1. 检疫防控：严禁从疫区调运葡萄苗木；"
                "2. 农业防治：选用抗根瘤蚜砧木（如SO4、5BB等）嫁接栽培；"
                "3. 化学防治：发生初期用辛硫磷、毒死蜱等灌根处理。"
                "在根瘤蚜疫区，使用抗性砧木是最根本的防治措施。"
            ),
            "colomerus_vitis": (
                "【葡萄缺节瘿螨（葡萄锈壁虱）】为害葡萄叶片形成毛毡状斑。防治方法："
                "1. 农业防治：冬季清园，刮除老树皮，烧毁病枝叶；"
                "2. 化学防治：萌芽前喷施石硫合剂（3-5波美度），生长期可选用阿维菌素、哒螨灵等。"
            ),
            "brevipalpus_lewisi": (
                "【南天竹刘氏短须螨】为害葡萄等多种植物。防治方法："
                "冬季清园喷施石硫合剂，生长期选用阿维菌素、哒螨灵、联苯肼酯等药剂喷雾。"
            ),
            "oides_decempunctata": (
                "【十星叶甲（葡萄十星叶甲）】成虫和幼虫均取食葡萄叶片。防治方法："
                "1. 农业防治：冬季清园，摘除有虫叶片；"
                "2. 化学防治：幼虫低龄期喷施高效氯氟氰菊酯、毒死蜱等。"
            ),
            "polyphagotarsonemus_latus": (
                "【侧多食附线螨（茶黄螨）】为害嫩叶和幼果，造成畸形。防治方法："
                "1. 农业防治：清除杂草和病残体；"
                "2. 化学防治：发生初期喷施阿维菌素、哒螨灵、联苯肼酯等，重点喷施嫩梢和嫩叶背面。"
            ),
            "pseudococcus_comstocki": (
                "【康氏粉蚧】刺吸式害虫，排泄蜜露引发煤污病。防治方法："
                "1. 农业防治：冬季刮除老树皮消灭越冬虫体；"
                "2. 生物防治：释放跳小蜂等天敌；"
                "3. 化学防治：若虫孵化盛期（第一代若虫期）施药效果最佳，可选用噻虫嗪、吡虫啉、螺虫乙酯等。"
            ),
            "parathrene_regalis": (
                "【葡萄透翅蛾】幼虫蛀入葡萄枝蔓内部为害。防治方法："
                "1. 农业防治：冬季修剪时剪除虫枝并烧毁；"
                "2. 化学防治：成虫羽化期和幼虫孵化期喷施高效氯氟氰菊酯等药剂，或用注射器向虫孔注入药剂。"
            ),
            "ampelophaga": (
                "【葡萄天蛾】幼虫取食叶片，大龄幼虫食量大。防治方法："
                "1. 农业防治：冬季深翻土壤灭蛹，人工捕杀幼虫；"
                "2. 化学防治：幼虫低龄期喷施高效氯氟氰菊酯、Bt制剂等。"
            ),
            "lycorma_delicatula": (
                "【斑衣蜡蝉】刺吸式害虫，为害葡萄、臭椿等。防治方法："
                "1. 农业防治：清除臭椿等寄主植物，冬季刮除卵块；"
                "2. 化学防治：若虫期喷施高效氯氟氰菊酯、吡虫啉等药剂。"
            ),
            "xylotrechus": (
                "【四带虎天牛】幼虫蛀干为害。防治方法："
                "1. 农业防治：加强树势管理，及时清除受害枝干；"
                "2. 化学防治：成虫羽化期喷施高效氯氟氰菊酯，幼虫期用药剂塞入虫孔或用注射器注入药剂后封口。"
            ),

            # ========== 果树害虫 (69-72) ==========
            "cicadella_viridis": (
                "【大青叶蝉】刺吸式害虫，成虫产卵刺伤枝干皮层造成伤痕。防治方法："
                "1. 农业防治：清除果园杂草（越冬场所），树干涂白防止产卵；"
                "2. 物理防治：灯光诱杀成虫；"
                "3. 化学防治：成虫盛发期喷施高效氯氟氰菊酯、吡虫啉等。"
                "10月上中旬成虫迁移到果树产卵前是防治关键期。"
            ),
            "miridae": (
                "【盲蝽科】刺吸式害虫，为害多种作物嫩芽、嫩叶和果实。防治方法："
                "清除田间杂草，若虫期喷施高效氯氟氰菊酯、吡虫啉等药剂。"
            ),
            "trialeurodes_vaporariorum": (
                "【温室粉虱（白粉虱）】刺吸式害虫，排泄蜜露引发煤污病，传播病毒。防治方法："
                "1. 物理防治：黄色粘虫板诱杀（温室大棚内每亩挂30-40块）；"
                "2. 生物防治：释放丽蚜小蜂（每亩1-2万头）；"
                "3. 化学防治：若虫期喷施噻虫嗪、吡虫啉、螺虫乙酯、氟啶虫胺腈等，注意喷施叶背面。"
                "粉虱世代重叠严重，需连续防治2-3次。"
            ),
            "erythroneura_apicalis": (
                "【斑叶蝉（葡萄斑叶蝉）】刺吸式害虫，为害葡萄、苹果等果树叶片。防治方法："
                "1. 农业防治：冬季清园，清除落叶杂草；"
                "2. 化学防治：若虫期喷施吡虫啉、噻虫嗪等药剂。"
            ),

            # ========== 柑橘害虫 (73-92) ==========
            "papilio_xuthus": (
                "【柑橘凤蝶】幼虫取食柑橘嫩叶。防治方法："
                "1. 农业防治：人工摘除卵和幼虫（幼龄幼虫形似鸟粪易识别）；"
                "2. 生物防治：保护寄生蜂天敌；"
                "3. 化学防治：幼虫低龄期喷施高效氯氟氰菊酯、Bt制剂等。"
                "柑橘凤蝶通常种群数量不大，以人工防治和生物防治为主。"
            ),
            "panonychus_citri": (
                "【柑橘红蜘蛛（柑橘全爪螨）】柑橘最严重害虫之一，刺吸叶片和果实汁液。防治方法："
                "1. 农业防治：合理灌溉增加果园湿度，种植覆盖植物；"
                "2. 生物防治：释放捕食螨（胡瓜钝绥螨等，每叶1-2头天敌即可控制）；"
                "3. 化学防治：春季和秋季高峰期重点防治，可选用阿维菌素、哒螨灵、螺螨酯、联苯肼酯、乙螨唑等。"
                "注意轮换用药，避免产生抗药性。柑橘红蜘蛛世代短、繁殖快，需定期监测。"
            ),
            "phyllocoptes_oleiverus": (
                "【柑橘锈螨（柑橘锈壁虱）】为害果实和叶片，使果皮变为锈褐色（黑皮果）。防治方法："
                "1. 农业防治：合理修剪保持通风透光，干旱季节适当喷灌；"
                "2. 化学防治：6-9月重点防治，可用阿维菌素、哒螨灵、螺螨酯等。"
                "高温干旱利于发生，发现个别果面有锈斑时立即施药。"
            ),
            "icerya_purchasi": (
                "【吹绵蚧】刺吸式害虫，排泄蜜露引发煤污病。防治方法："
                "1. 生物防治：释放澳洲瓢虫（吹绵蚧的重要天敌，防治效果极佳）；"
                "2. 化学防治：若虫孵化盛期喷施噻虫嗪、吡虫啉、矿物油乳剂等。"
                "澳洲瓢虫是经典生物防治案例，有条件地区优先采用。"
            ),
            "unaspis_yanonensis": (
                "【矢尖蚧】柑橘重要盾蚧类害虫，刺吸枝干、叶片和果实汁液。防治方法："
                "1. 农业防治：合理修剪改善通风透光，剪除虫枝烧毁；"
                "2. 生物防治：保护矢尖蚧黄蚜小蜂等天敌；"
                "3. 化学防治：第一代若虫孵化盛期（5-6月）是关键防治时期，可选用噻虫嗪、螺虫乙酯、矿物油乳剂等。"
            ),
            "ceroplastes_rubens": (
                "【红蜡蚧（红蚧）】刺吸式害虫，虫体覆盖红色蜡壳。防治方法："
                "若虫孵化盛期（6-7月）喷施噻虫嗪、螺虫乙酯、矿物油乳剂等。"
                "蜡壳形成后药剂难渗透，必须在若虫期（蜡壳未形成前）施药。"
            ),
            "chrysomphalus_aonidum": (
                "【黑褐圆盾蚧】刺吸式害虫，严重时造成枝梢枯死。防治方法："
                "同矢尖蚧，第一代若虫期是防治关键。冬季可喷施松脂合剂清园。"
            ),
            "parlatoria_zizyphus": (
                "【黑点介壳虫（黑点蚧）】刺吸式害虫，为害柑橘叶片和果实。防治方法："
                "若虫期施药防治，药剂同矢尖蚧。结合冬季修剪剪除虫枝。"
            ),
            "nipaecoccus_vastalor": (
                "【堆蜡粉蚧】刺吸式害虫，虫体覆盖白色蜡粉。防治方法："
                "若虫孵化盛期喷施噻虫嗪、螺虫乙酯、矿物油乳剂等。保护跳小蜂等天敌。"
            ),
            "aleurocanthus_spiniferus": (
                "【黑刺粉虱】刺吸式害虫，排泄蜜露引发煤污病。防治方法："
                "1. 生物防治：保护粉虱细蜂等天敌；"
                "2. 化学防治：若虫盛发期喷施噻虫嗪、吡虫啉、螺虫乙酯等。"
                "黑刺粉虱天敌丰富，尽量减少广谱性杀虫剂的使用。"
            ),
            "bactrocera_minax": (
                "【柑橘大实蝇】检疫性害虫，幼虫蛀食果肉造成落果。防治方法："
                "1. 检疫防控：严禁从疫区调运带虫果实；"
                "2. 农业防治：及时捡拾和销毁落果（深埋或水煮），冬季深翻土壤灭蛹；"
                "3. 化学防治：成虫羽化期（5-6月）用蛋白诱饵+敌百虫喷洒树冠诱杀成虫。"
            ),
            "dacus_dorsalis": (
                "【柑桔小实蝇（橘小实蝇）】危险性检疫害虫，寄主广泛。防治方法："
                "1. 农业防治：及时清除落果和虫果，果实套袋；"
                "2. 物理防治：甲基丁香酚诱杀雄虫（每亩3-5个诱捕器），黄色粘板诱杀；"
                "3. 化学防治：蛋白诱饵+杀虫剂喷洒诱杀成虫。"
                "综合运用多种方法，以诱杀和田园清洁为主。"
            ),
            "bactrocera_tsuneonis": (
                "【蜜柑大实蝇】幼虫蛀食蜜柑果实。防治方法同柑橘大实蝇："
                "销毁落果、捡拾虫果，成虫期用蛋白诱饵+杀虫剂诱杀。"
            ),
            "prodenia_litura": (
                "【斜纹夜蛾】暴食性害虫，幼虫取食多种作物叶片。防治方法："
                "1. 农业防治：清除田间杂草和残株；"
                "2. 物理防治：灯光诱杀成虫，性诱剂诱杀；"
                "3. 生物防治：使用斜纹夜蛾核型多角体病毒、Bt制剂；"
                "4. 化学防治：幼虫3龄前施药效果最好，可选用甲维盐、氯虫苯甲酰胺、茚虫威、虫螨腈等。"
            ),
            "adristyranus": (
                "【枯叶夜蛾（鸟嘴壶夜蛾）】成虫吸食成熟果实汁液造成烂果。防治方法："
                "1. 农业防治：清除果园周边野生寄主植物（木防己等）；"
                "2. 物理防治：灯光诱杀成虫，果实套袋；"
                "3. 化学防治：果实成熟期傍晚喷施高效氯氟氰菊酯等趋避剂。"
            ),
            "phyllocnistis_citrella": (
                "【柑桔潜叶蛾】幼虫潜入嫩叶表皮取食形成银白色隧道，造成叶片卷曲，并为溃疡病提供侵入口。防治方法："
                "1. 农业防治：统一放梢（抹除零星嫩梢，统一留梢），减少虫源；"
                "2. 化学防治：新梢抽发1-2cm时施药保护，可选用阿维菌素、高效氯氟氰菊酯、吡虫啉等。"
                "以保护新梢为目的，施药关键在于\"抹芽控梢，统一放梢，适时施药\"。"
            ),
            "toxoptera_citricidus": (
                "【花椒蚜虫（橘蚜）】刺吸式害虫，为害新梢和嫩叶，传播柑橘衰退病毒。防治方法："
                "1. 生物防治：保护瓢虫、草蛉、食蚜蝇等天敌；"
                "2. 化学防治：新梢有蚜率达20%时施药，可选用吡虫啉、啶虫脒、氟啶虫胺腈等。"
            ),
            "toxoptera_aurantii": (
                "【茶蚜（二叉蚜）】刺吸式害虫，为害茶树、柑橘等植物新梢。防治方法同橘蚜："
                "保护天敌，必要时喷施吡虫啉、啶虫脒等药剂。"
            ),
            "aphis_citricola": (
                "【绣线菊蚜（苹果黄蚜）】刺吸式害虫，为害柑橘、苹果等多种果树新梢。防治方法："
                "同橘蚜，保护天敌为主，药剂防治为辅。"
            ),
            "scirtothrips_dorsalis": (
                "【茶黄蓟马】锉吸式害虫，为害嫩叶和幼果，造成银白色疤痕。防治方法："
                "1. 农业防治：清除杂草减少虫源；"
                "2. 化学防治：若虫盛发期喷施乙基多杀菌素、阿维菌素、吡虫啉等。"
            ),

            # ========== 荔枝/龙眼害虫 (93-95) ==========
            "dasineura_sp": (
                "【荔枝叶瘿蚊】幼虫为害嫩叶形成疱状虫瘿（小瘤状突起）。防治方法："
                "1. 农业防治：冬季剪除虫瘿枝叶并烧毁；"
                "2. 化学防治：新梢抽发期喷施高效氯氟氰菊酯、阿维菌素等药剂保护嫩叶。"
            ),
            "lawana_imitata": (
                "【白翅蜡蝉】刺吸式害虫，若虫分泌白色蜡丝，影响树势。防治方法："
                "1. 农业防治：修剪虫枝，清除杂草；"
                "2. 化学防治：若虫期喷施高效氯氟氰菊酯、吡虫啉等药剂。"
            ),
            "salurnis_marginella": (
                "【褐缘蛾蜡蝉】刺吸式害虫，若虫群集为害。防治方法同白翅蜡蝉："
                "修剪虫枝，若虫期喷施高效氯氟氰菊酯、吡虫啉等药剂。"
            ),

            # ========== 芒果害虫 (96-101) ==========
            "deporaus_marginatus": (
                "【芒果切叶象甲】成虫切食嫩叶，雌虫切断叶柄产卵。防治方法："
                "1. 农业防治：收集落地的切叶并烧毁（清除虫卵）；"
                "2. 化学防治：新梢抽发期喷施高效氯氟氰菊酯、毒死蜱等药剂保护嫩叶。"
            ),
            "chlumetia_transversa": (
                "【横线尾夜蛾（芒果横纹尾夜蛾）】幼虫蛀食嫩梢和花穗。防治方法："
                "1. 农业防治：剪除受害枯梢并烧毁；"
                "2. 化学防治：新梢和花穗抽发期喷施高效氯氟氰菊酯、甲维盐等药剂。"
            ),
            "mango_flat_beak_leafhopper": (
                "【叶蝉（芒果扁喙叶蝉）】刺吸式害虫，为害嫩叶和花穗，造成落花落果。防治方法："
                "1. 农业防治：合理修剪保持通风透光，清除果园杂草；"
                "2. 化学防治：花穗期和梢期重点防治，可选用吡虫啉、噻虫嗪、高效氯氟氰菊酯等。"
            ),
            "rhytidodera_bowrinii": (
                "【脊胸天牛】幼虫蛀干为害，造成枝干枯死甚至全株死亡。防治方法："
                "1. 农业防治：加强栽培管理增强树势，树干涂白；"
                "2. 物理防治：人工捕杀成虫，用铁丝刺杀蛀道内幼虫；"
                "3. 化学防治：用药剂（敌敌畏、毒死蜱等）注入虫孔后用泥土封口熏杀幼虫。"
            ),
            "sternochetus_frigidus": (
                "【芒果果肉象甲】幼虫蛀入果核内为害，造成落果。防治方法："
                "1. 农业防治：捡拾落果并销毁，冬季深翻灭蛹；"
                "2. 化学防治：成虫出土期和产卵期喷施高效氯氟氰菊酯等药剂。"
            ),
            "cicadellidae": (
                "【叶蝉科】刺吸式害虫，为害多种作物叶片，传播植物病毒。防治方法："
                "1. 农业防治：清除田间杂草（越冬和中间寄主）；"
                "2. 物理防治：灯光诱杀（黑光灯或频振式杀虫灯）；"
                "3. 化学防治：若虫期喷施吡虫啉、噻虫嗪、异丙威等药剂。"
                "对于传毒叶蝉，以\"治虫防病\"为原则，在传毒前控制虫口密度。"
            ),
        }

        return treatment_advice.get(class_name, default_advice)

    def detect_single_image(self, 
                           image_path: str, 
                           user_id: Optional[str] = None,
                           model_name: str = "agri-pest-yolo11n",
                           minio_svc = None) -> DetectionResult:
        """
        单图目标检测

        参数：
            image_path: 图片文件路径
            user_id: 用户 ID（可选）
            model_name: 模型名称（可选）

        返回：
            DetectionResult: 检测结果对象

        检测流程：
            1. 记录开始时间
            2. 生成唯一检测 ID
            3. 调用 YOLO 模型进行预测
            4. 解析检测框信息
            5. 在图片上绘制检测框
            6. 上传结果图片到 MinIO
            7. 计算检测耗时
            8. 保存检测记录到数据库
            9. 返回检测结果

        说明：
            - 使用配置文件中的置信度和 IOU 阈值
            - 检测结果包含所有检测到的目标
            - 结果图片上传到 MinIO 对象存储
            - 检测记录持久化存储到 PostgreSQL 数据库
        """
        # 记录检测开始时间
        start_time = time.time()

        _ensure_ml_imports()  # 确保重型依赖已导入

        # 如果模型未加载，延迟加载
        if self.model is None:
            self._load_model_smart()

        # 生成唯一的检测 ID
        detection_id = str(uuid.uuid4())

        # 确定推理设备（优先 GPU）
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"

        # 调用 YOLO 模型进行预测（优化：限制图片尺寸加快推理）
        results = self.model.predict(
            source=image_path,
            conf=settings.confidence_threshold,
            iou=settings.iou_threshold,
            imgsz=640,              # 推理尺寸，YOLO11n 推荐 640
            device=device,           # GPU 加速
            half=(device == "cuda"), # GPU 时启用 FP16 半精度
            save=False
        )

        # 解析检测结果
        boxes = []  # 检测框列表
        db_results = []  # 数据库结果列表

        # 遍历所有检测结果
        for result in results:
            # 遍历所有检测到的目标框
            for box in result.boxes:
                # 提取检测框坐标（xyxy 格式：左上角、右下角）
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                # 提取置信度
                confidence = float(box.conf[0])

                # 提取类别 ID
                class_id = int(box.cls[0])

                # 获取类别名称
                class_name = self.class_names.get(class_id, f"class_{class_id}")

                # 获取中文名称
                chinese_name = self.get_class_chinese_name(class_name)

                # 获取AI防治建议
                treatment_advice = self.get_treatment_advice(class_name)

                # 创建检测框对象（用于返回）
                boxes.append(DetectionBox(
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                    confidence=confidence,
                    class_id=class_id,
                    class_name=class_name,
                    chinese_name=chinese_name,
                    treatment_advice=treatment_advice
                ))

                # 创建数据库结果对象（用于持久化）
                db_results.append(DBDetectionResult(
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                    confidence=confidence,
                    class_id=class_id,
                    class_name=class_name,
                    chinese_name=chinese_name
                ))

        # 生成结果文件名
        result_filename = f"result_{uuid.uuid4().hex}.jpg"

        # 手动绘制检测框，Pillow 支持中文标签
        from PIL import Image, ImageDraw, ImageFont
        annotated_image_bgr = cv2.imread(image_path)
        annotated_image_rgb = cv2.cvtColor(annotated_image_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(annotated_image_rgb)
        draw = ImageDraw.Draw(pil_img)
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 18)
        except Exception:
            try:
                font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttf", 18)
            except Exception:
                font = ImageFont.load_default()
        for box in boxes:
            x1, y1, x2, y2 = int(box.x1), int(box.y1), int(box.x2), int(box.y2)
            text = f"{box.chinese_name} {box.confidence:.2f}"
            draw.rectangle([(x1, y1), (x2, y2)], outline=(0, 255, 0), width=2)
            text_y = max(y1 - 18, 0)
            bbox = draw.textbbox((x1, text_y), text, font=font)
            draw.rectangle(bbox, fill=(0, 255, 0))
            draw.text((x1, text_y), text, fill=(0, 0, 0), font=font)
        annotated_image_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        _, image_bytes = cv2.imencode('.jpg', annotated_image_bgr)
        image_bytes = image_bytes.tobytes()

        # 使用传入的 minio_svc 或全局的 minio_service
        minio = minio_svc if minio_svc is not None else minio_service

        # 上传结果图片到 MinIO
        result_object_name = minio.upload_result_image(image_bytes, "jpg")

        # 计算检测耗时
        detection_time = time.time() - start_time

        # 获取原始图片文件名
        image_filename = os.path.basename(image_path)

        # 将原始图片上传到 MinIO
        with open(image_path, 'rb') as f:
            original_image_bytes = f.read()
        original_object_name = minio.upload_image_bytes(original_image_bytes, image_filename)

        # 构建 MinIO 对象 key
        original_image_key = f"uploads/{original_object_name}"
        result_image_key = f"results/{result_object_name}"

        # 保存检测记录到数据库
        db_record = self._save_to_database(
            user_id=user_id,
            detection_id=detection_id,
            model_name=model_name,
            total_objects=len(boxes),
            detection_time=detection_time,
            original_image_key=original_image_key,
            result_image_key=result_image_key,
            results=db_results
        )

        # 构建图片 URL：使用相对路径，由 nginx 代理
        if minio.is_available:
            original_image_url = f"/api/detection/files/agri-pest-original/{original_object_name}"
            result_image_url = f"/api/detection/files/agri-pest-results/{result_object_name}"
        else:
            original_image_url = f"/static/uploads/{original_object_name}"
            result_image_url = f"/static/results/{result_object_name}"

        # 构建检测结果对象
        return DetectionResult(
            detection_id=detection_id,                    # 唯一检测 ID
            image_url=original_image_url,                 # 原始图片 URL（FastAPI代理）
            result_image_url=result_image_url,            # 结果图片 URL（FastAPI代理）
            boxes=boxes,                                 # 检测框列表
            total_objects=len(boxes),                    # 检测到的目标数量
            detection_time=round(detection_time, 3),     # 检测耗时（秒）
            model_name=model_name,                       # 使用的模型名称
            created_at=datetime.now()                   # 创建时间
        )

    def _save_to_database(self,
                         user_id: Optional[str],
                         detection_id: str,
                         model_name: str,
                         total_objects: int,
                         detection_time: float,
                         original_image_key: str,
                         result_image_key: str,
                         results: List[DBDetectionResult]) -> DetectionRecord:
        """
        将检测记录保存到数据库

        参数：
            user_id: 用户 ID
            detection_id: 检测 ID
            model_name: 模型名称
            total_objects: 检测到的目标数量
            detection_time: 检测耗时
            original_image_key: 原始图片 key
            result_image_key: 结果图片 key
            results: 检测结果列表

        返回：
            DetectionRecord: 数据库记录对象
        """
        try:
            # 获取数据库会话
            db = next(get_db())

            # 创建检测记录
            record = DetectionRecord(
                id=detection_id,
                user_id=user_id,
                type="single",
                status="completed",
                model_name=model_name,
                model_version="1.0.0",
                total_objects=total_objects,
                detection_time=detection_time,
                original_image_key=original_image_key,
                result_image_key=result_image_key
            )

            # 添加到会话
            db.add(record)

            # 添加检测结果
            for result in results:
                result.record_id = detection_id
                db.add(result)

            # 提交事务
            db.commit()

            # 刷新记录
            db.refresh(record)

            logger.info(f"检测记录已保存到数据库: {detection_id}")

            return record

        except Exception as e:
            logger.error(f"保存检测记录到数据库失败: {str(e)}")
            # 回滚事务
            try:
                db.rollback()
            except:
                pass
            return None

    def get_detection_history(self, user_id: str = None, limit: int = 10) -> List[DetectionRecord]:
        """
        获取检测历史记录

        参数：
            user_id: 用户 ID（可选）
            limit: 返回数量限制（默认 10）

        返回：
            List[DetectionRecord]: 检测记录列表
        """
        try:
            db = next(get_db())

            query = db.query(DetectionRecord).order_by(DetectionRecord.created_at.desc())

            if user_id:
                query = query.filter(DetectionRecord.user_id == user_id)

            records = query.limit(limit).all()

            logger.info(f"获取检测历史记录: {len(records)} 条")

            return records

        except Exception as e:
            logger.error(f"获取检测历史记录失败: {str(e)}")
            return []

    def get_detection_by_id(self, detection_id: str) -> Optional[DetectionRecord]:
        """
        根据检测 ID 获取检测记录

        参数：
            detection_id: 检测 ID

        返回：
            Optional[DetectionRecord]: 检测记录对象
        """
        try:
            db = next(get_db())

            record = db.query(DetectionRecord).filter(DetectionRecord.id == detection_id).first()

            if record:
                logger.info(f"获取检测记录成功: {detection_id}")
            else:
                logger.warning(f"检测记录不存在: {detection_id}")

            return record

        except Exception as e:
            logger.error(f"获取检测记录失败: {str(e)}")
            return None

    def delete_detection(self, detection_id: str) -> bool:
        """
        删除检测记录

        参数：
            detection_id: 检测 ID

        返回：
            bool: 删除是否成功
        """
        try:
            db = next(get_db())

            record = db.query(DetectionRecord).filter(DetectionRecord.id == detection_id).first()

            if record:
                # 先取出 MinIO 文件 key，以便删除记录后清理文件
                original_key = record.original_image_key
                result_key = record.result_image_key

                # 删除关联的检测结果
                db.query(DBDetectionResult).filter(DBDetectionResult.record_id == detection_id).delete()

                # 删除检测记录
                db.delete(record)

                # 提交事务
                db.commit()

                # 删除 MinIO 上的图片文件
                for key in [original_key, result_key]:
                    if key:
                        try:
                            object_name = os.path.basename(key)
                            bucket = "agri-pest-results" if "result" in key.lower() else "agri-pest-original"
                            minio_service.delete_object(bucket, object_name)
                        except Exception as e:
                            logger.warning(f"删除 MinIO 文件失败 [{key}]: {str(e)}")

                logger.info(f"检测记录已删除: {detection_id}")
                return True

            logger.warning(f"检测记录不存在: {detection_id}")
            return False

        except Exception as e:
            logger.error(f"删除检测记录失败: {str(e)}")
            try:
                db.rollback()
            except:
                pass
            return False

    def detect_frame_realtime(self, image, confidence_threshold=None, iou_threshold=None):
        """
        实时视频帧检测（不保存到数据库，不保存文件）

        参数：
            image: numpy 数组格式的图片（BGR 格式，来自 cv2）
            confidence_threshold: 置信度阈值（可选，默认使用配置值）
            iou_threshold: IOU 阈值（可选，默认使用配置值）

        返回：
            dict: 包含 boxes, total_objects, detection_time, image_width, image_height
        """
        _ensure_ml_imports()

        if self.model is None:
            self._load_model_smart()

        conf = confidence_threshold if confidence_threshold is not None else settings.confidence_threshold
        iou_val = iou_threshold if iou_threshold is not None else settings.iou_threshold

        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"

        start_time = time.time()

        results = self.model.predict(
            source=image,
            conf=conf,
            iou=iou_val,
            imgsz=640,
            device=device,
            half=(device == "cuda"),
            save=False
        )

        boxes = []
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = self.class_names.get(class_id, f"class_{class_id}")
                chinese_name = self.get_class_chinese_name(class_name)

                boxes.append(DetectionBox(
                    x1=round(x1, 2),
                    y1=round(y1, 2),
                    x2=round(x2, 2),
                    y2=round(y2, 2),
                    confidence=round(confidence, 4),
                    class_id=class_id,
                    class_name=class_name,
                    chinese_name=chinese_name
                ))

        detection_time = time.time() - start_time

        return {
            "boxes": boxes,
            "total_objects": len(boxes),
            "detection_time": round(detection_time, 4),
            "image_width": image.shape[1] if len(image.shape) >= 2 else 0,
            "image_height": image.shape[0] if len(image.shape) >= 2 else 0
        }


# =============================================================================
# 全局检测服务实例
# =============================================================================
# 创建全局唯一的检测服务实例（单例模式）
# 在应用的任何地方都可以通过 import detection_service 访问
detection_service = DetectionService()
