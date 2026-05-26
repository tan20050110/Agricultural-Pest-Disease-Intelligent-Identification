# =============================================================================
# 病害识别服务模块
# =============================================================================
# 功能说明：
#   - 封装 ResNet50 病害分类模型的所有操作
#   - 提供单图病害识别接口
#   - 支持 Top-5 预测结果返回
#
# ResNet50 模型说明：
#   ResNet50（Residual Network 50）是一种深度残差网络，共 50 层
#   本模块使用基于 PlantVillage 数据集训练的 ResNet50 分类模型
#   支持识别 39 种农作物病害/健康状态
#   验证准确率：99.92%
#
# 推理流程：
#   1. 加载图片并预处理（resize、normalize）
#   2. 调用 ResNet50 进行前向推理
#   3. Softmax 得到类别概率分布
#   4. 取 Top-5 预测结果
#   5. 保存记录到数据库
#   6. 返回预测结果
# =============================================================================

import json
import os
import time
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import torch
import torch.nn as nn
import torchvision.transforms as transforms

# 延迟导入 OpenCV
cv2 = None

def _ensure_cv2():
    """延迟导入 OpenCV"""
    global cv2
    if cv2 is None:
        import cv2 as _cv2
        cv2 = _cv2

from app.config import settings
from app.models.schemas import DiseasePrediction, DiseaseResult
from app.models.database import DetectionRecord, get_db
from app.services.minio_service import minio_service

logger = logging.getLogger(__name__)


class DiseaseService:
    """
    病害分类服务类

    该类封装了 ResNet50 病害分类的所有操作，包括：
    - 模型加载和初始化
    - 图片预处理
    - 单图病害分类
    - 预测结果持久化存储
    """

    # 图片预处理参数（ImageNet 标准）
    IMG_SIZE = 224
    MEAN = [0.485, 0.456, 0.406]
    STD = [0.229, 0.224, 0.225]

    # 病害类别中文名称映射
    DISEASE_CN_NAMES = {
        "Apple___Apple_scab": "苹果黑星病",
        "Apple___Black_rot": "苹果黑腐病",
        "Apple___Cedar_apple_rust": "苹果锈病",
        "Apple___healthy": "苹果健康",
        "Background_without_leaves": "无叶片背景",
        "Blueberry___healthy": "蓝莓健康",
        "Cherry___Powdery_mildew": "樱桃白粉病",
        "Cherry___healthy": "樱桃健康",
        "Corn___Cercospora_leaf_spot Gray_leaf_spot": "玉米灰斑病",
        "Corn___Common_rust": "玉米锈病",
        "Corn___Northern_Leaf_Blight": "玉米大斑病",
        "Corn___healthy": "玉米健康",
        "Grape___Black_rot": "葡萄黑腐病",
        "Grape___Esca_(Black_Measles)": "葡萄黑麻疹病",
        "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": "葡萄叶斑病",
        "Grape___healthy": "葡萄健康",
        "Orange___Haunglongbing_(Citrus_greening)": "柑橘黄龙病",
        "Peach___Bacterial_spot": "桃细菌性斑点病",
        "Peach___healthy": "桃健康",
        "Pepper,_bell___Bacterial_spot": "甜椒细菌性斑点病",
        "Pepper,_bell___healthy": "甜椒健康",
        "Potato___Early_blight": "马铃薯早疫病",
        "Potato___Late_blight": "马铃薯晚疫病",
        "Potato___healthy": "马铃薯健康",
        "Raspberry___healthy": "覆盆子健康",
        "Soybean___healthy": "大豆健康",
        "Squash___Powdery_mildew": "南瓜白粉病",
        "Strawberry___Leaf_scorch": "草莓叶枯病",
        "Strawberry___healthy": "草莓健康",
        "Tomato___Bacterial_spot": "番茄细菌性斑点病",
        "Tomato___Early_blight": "番茄早疫病",
        "Tomato___Late_blight": "番茄晚疫病",
        "Tomato___Leaf_Mold": "番茄叶霉病",
        "Tomato___Septoria_leaf_spot": "番茄斑枯病",
        "Tomato___Spider_mites Two-spotted_spider_mite": "番茄红蜘蛛",
        "Tomato___Target_Spot": "番茄斑点病",
        "Tomato___Tomato_Yellow_Leaf_Curl_Virus": "番茄黄化曲叶病毒病",
        "Tomato___Tomato_mosaic_virus": "番茄花叶病毒病",
        "Tomato___healthy": "番茄健康",
    }

    # 病害防治建议映射
    DISEASE_ADVICE = {
        "Apple___Apple_scab": (
            "【苹果黑星病（疮痂病）】由真菌引起的叶片和果实病害。防治方法："
            "1. 农业防治：秋季清除落叶和病果并集中烧毁，合理修剪改善通风透光；"
            "2. 化学防治：萌芽前喷施波尔多液（3-5波美度石硫合剂），生长期可选用苯醚甲环唑、戊唑醇、吡唑醚菌酯等。"
            "关键防治时期为春季新梢生长期和花后。"
        ),
        "Apple___Black_rot": (
            "【苹果黑腐病】真菌性病害，为害叶片、果实和枝干。防治方法："
            "1. 农业防治：修剪病枝并销毁，清除僵果，合理施肥增强树势；"
            "2. 化学防治：花前和花后喷施苯醚甲环唑、甲基硫菌灵、吡唑醚菌酯、代森锰锌等。"
            "注意防治枝干溃疡病斑（病菌越冬场所）。"
        ),
        "Apple___Cedar_apple_rust": (
            "【苹果锈病（赤星病）】转主寄主病害，需桧柏完成侵染循环。防治方法："
            "1. 农业防治：铲除果园周边5km内的桧柏（转主寄主），或在桧柏上喷药防治冬孢子角；"
            "2. 化学防治：苹果展叶至花后喷施三唑酮、苯醚甲环唑、戊唑醇等三唑类杀菌剂。"
            "关键：消灭转主寄主是最根本的防治措施。"
        ),
        "Apple___healthy": "苹果叶片状态健康，无需特殊处理。继续保持良好的田间管理和病虫害监测即可。",
        "Background_without_leaves": "未检测到叶片，请确保图片中包含完整的作物叶片，以便进行准确的病害诊断。",
        "Blueberry___healthy": "蓝莓叶片状态健康，无需特殊处理。继续保持良好的水肥管理即可。",
        "Cherry___Powdery_mildew": (
            "【樱桃白粉病】真菌性病害，叶片和嫩梢覆盖白色粉状物。防治方法："
            "1. 农业防治：合理修剪保持通风透光，增施磷钾肥增强抗病性；"
            "2. 化学防治：发病初期喷施三唑酮、苯醚甲环唑、吡唑醚菌酯、硫磺制剂等。"
            "温暖干燥天气利于白粉病发生，需加强监测。"
        ),
        "Cherry___healthy": "樱桃叶片状态健康，无需特殊处理。注意定期巡查果园，做好预防工作。",
        "Corn___Cercospora_leaf_spot Gray_leaf_spot": (
            "【玉米灰斑病】真菌性病害，叶片上出现灰色矩形病斑。防治方法："
            "1. 农业防治：选用抗病品种，合理轮作，收获后清除病残体；"
            "2. 化学防治：发病初期喷施苯醚甲环唑、丙环唑、吡唑醚菌酯、嘧菌酯等。"
            "玉米大喇叭口期至抽雄期是防治关键期。"
        ),
        "Corn___Common_rust": (
            "【玉米锈病（普通锈病）】真菌性病害，叶片出现铁锈色夏孢子堆。防治方法："
            "1. 农业防治：选用抗病品种，合理密植，增施磷钾肥；"
            "2. 化学防治：发病初期喷施三唑酮、戊唑醇、苯醚甲环唑等三唑类杀菌剂。"
            "高温高湿条件利于锈病流行，需在发病初期及时用药。"
        ),
        "Corn___Northern_Leaf_Blight": (
            "【玉米大斑病】真菌性病害，叶片形成大型梭形灰褐色病斑。防治方法："
            "1. 农业防治：选用抗病品种（含Ht抗性基因），清除病残体，合理轮作；"
            "2. 化学防治：发病初期喷施苯醚甲环唑、吡唑醚菌酯、嘧菌酯、代森锰锌等。"
            "防治适期为玉米大喇叭口期至抽雄期。"
        ),
        "Corn___healthy": "玉米叶片状态健康，无需特殊处理。继续做好田间管理和病虫害监测。",
        "Grape___Black_rot": (
            "【葡萄黑腐病】真菌性病害，为害果实和叶片。防治方法："
            "1. 农业防治：冬季清园，剪除病枝病果并烧毁，合理修剪增加通风透光；"
            "2. 化学防治：花前、花后和果实膨大期喷施苯醚甲环唑、吡唑醚菌酯、代森锰锌、甲基硫菌灵等。"
        ),
        "Grape___Esca_(Black_Measles)": (
            "【葡萄黑麻疹病（埃斯卡病）】真菌复合侵染的枝干病害，造成叶片虎斑状坏死。防治方法："
            "1. 农业防治：合理修剪，避免大伤口，伤口涂抹保护剂；"
            "2. 化学防治：休眠期喷施波尔多液或石硫合剂，生长期做好预防。"
            "此病目前尚无特效药剂，以预防为主。严重病株建议及时挖除。"
        ),
        "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": (
            "【葡萄叶斑病】真菌性病害，叶片出现不规则褐色斑点。防治方法："
            "1. 农业防治：清除病叶和落叶，改善通风透光；"
            "2. 化学防治：发病初期喷施代森锰锌、苯醚甲环唑、吡唑醚菌酯等。"
        ),
        "Grape___healthy": "葡萄叶片状态健康，无需特殊处理。注意定期喷施保护性杀菌剂预防病害发生。",
        "Orange___Haunglongbing_(Citrus_greening)": (
            "【柑橘黄龙病】由韧皮部杆菌引起的毁灭性病害，是世界柑橘生产最严重的病害。防治方法："
            "1. 严格检疫：严禁从病区调运苗木和接穗，使用无病苗木；"
            "2. 防除木虱（传播媒介）：柑橘木虱是唯一传毒昆虫，可用吡虫啉、噻虫嗪、啶虫脒等药剂统一防治；"
            "3. 挖除病树：发现病株后立即挖除（先喷药杀木虱再砍树），防止扩散；"
            "4. 建立防护林带阻隔木虱迁移。"
            "黄龙病目前无法治愈，\"及时挖除病树+防除木虱+种植无病苗\"是公认的防控三原则。"
        ),
        "Peach___Bacterial_spot": (
            "【桃细菌性穿孔病】细菌性病害，叶片形成穿孔，果实出现褐色斑点。防治方法："
            "1. 农业防治：清除病枝病叶，合理修剪，增施有机肥；"
            "2. 化学防治：萌芽前喷施波尔多液或石硫合剂，生长期选用春雷霉素、噻唑锌、氢氧化铜等。"
            "风雨天气有利于细菌传播，雨前雨后及时喷药保护。"
        ),
        "Peach___healthy": "桃树叶片状态健康，无需特殊处理。继续做好果园管理和病虫害监测。",
        "Pepper,_bell___Bacterial_spot": (
            "【甜椒细菌性斑点病（疮痂病）】细菌性病害，叶片和果实出现水渍状斑点。防治方法："
            "1. 农业防治：种子消毒（温汤浸种），合理轮作，清除病残体；"
            "2. 化学防治：发病初期喷施春雷霉素、氢氧化铜、噻菌铜等铜制剂或抗生素类药剂。"
        ),
        "Pepper,_bell___healthy": "甜椒叶片状态健康，无需特殊处理。继续做好田间管理和病虫害预防。",
        "Potato___Early_blight": (
            "【马铃薯早疫病】真菌性病害，叶片形成同心轮纹状褐色病斑。防治方法："
            "1. 农业防治：选用抗病品种，增施磷钾肥，合理灌溉；"
            "2. 化学防治：发病初期喷施苯醚甲环唑、嘧菌酯、吡唑醚菌酯、代森锰锌等。"
            "早疫病多在植株生长后期、营养不足时发生，加强水肥管理是重要预防措施。"
        ),
        "Potato___Late_blight": (
            "【马铃薯晚疫病】毁灭性卵菌病害，曾引发了爱尔兰大饥荒。防治方法："
            "1. 农业防治：选用抗病品种，合理轮作，销毁带病种薯；"
            "2. 化学防治：以预防为主，在现蕾至开花期喷施霜脲·锰锌、烯酰吗啉、氟噻唑吡乙酮、霜霉威等。"
            "晚疫病传播极快，阴雨高湿天气需提前预防。建议建立预警系统指导用药。"
        ),
        "Potato___healthy": "马铃薯叶片状态健康，无需特殊处理。晚疫病流行季节注意预防性喷药保护。",
        "Raspberry___healthy": "覆盆子叶片状态健康，无需特殊处理。继续做好田间管理。",
        "Soybean___healthy": "大豆叶片状态健康，无需特殊处理。继续做好田间管理和病虫害监测。",
        "Squash___Powdery_mildew": (
            "【南瓜白粉病】真菌性病害，叶片覆盖白色粉状物，严重时叶片枯黄。防治方法："
            "1. 农业防治：合理密植保持通风，增施磷钾肥；"
            "2. 化学防治：发病初期喷施三唑酮、吡唑醚菌酯、醚菌酯、硫磺制剂等。"
        ),
        "Strawberry___Leaf_scorch": (
            "【草莓叶枯病（叶焦病）】真菌性病害，叶片边缘焦枯变褐。防治方法："
            "1. 农业防治：清除病叶和老叶，合理密植保持通风，避免过度灌溉；"
            "2. 化学防治：发病初期喷施苯醚甲环唑、吡唑醚菌酯、甲基硫菌灵等。"
        ),
        "Strawberry___healthy": "草莓叶片状态健康，无需特殊处理。继续做好日常管理和病虫害预防。",
        "Tomato___Bacterial_spot": (
            "【番茄细菌性斑点病】细菌性病害，叶片和果实出现黑色小斑点。防治方法："
            "1. 农业防治：种子消毒（55℃温汤浸种30分钟），合理轮作，清除病残体；"
            "2. 化学防治：发病初期喷施春雷霉素、氢氧化铜、噻菌铜、中生菌素等。"
        ),
        "Tomato___Early_blight": (
            "【番茄早疫病（轮纹病）】真菌性病害，叶片形成同心轮纹状褐色病斑。防治方法："
            "1. 农业防治：合理轮作，增施有机肥，及时摘除老叶病叶；"
            "2. 化学防治：发病初期喷施苯醚甲环唑、嘧菌酯、吡唑醚菌酯、代森锰锌等。"
        ),
        "Tomato___Late_blight": (
            "【番茄晚疫病】毁灭性卵菌病害，阴雨高湿天气迅速传播造成植株枯死。防治方法："
            "1. 农业防治：合理密植保持通风，避免叶面长时间湿润；"
            "2. 化学防治：以预防为主，发病前或发病初期喷施霜脲·锰锌、烯酰吗啉、氟噻唑吡乙酮、霜霉威等。"
            "注意：一旦出现中心病株，需立即全田喷药，阴雨天气隔5-7天再喷一次。"
        ),
        "Tomato___Leaf_Mold": (
            "【番茄叶霉病】真菌性病害，叶片背面出现灰紫色霉层。防治方法："
            "1. 农业防治：合理密植保持通风，降低棚内湿度；"
            "2. 化学防治：发病初期喷施苯醚甲环唑、吡唑醚菌酯、嘧菌酯、氟硅唑等。"
            "温室大棚内高湿环境利于叶霉病发生，加强通风排湿是重要防控措施。"
        ),
        "Tomato___Septoria_leaf_spot": (
            "【番茄斑枯病（白星病）】真菌性病害，叶片出现圆形灰白色小斑点。防治方法："
            "1. 农业防治：清除病残体，合理轮作（与非茄科作物轮作3年以上）；"
            "2. 化学防治：发病初期喷施苯醚甲环唑、代森锰锌、吡唑醚菌酯等。"
        ),
        "Tomato___Spider_mites Two-spotted_spider_mite": (
            "【番茄红蜘蛛（二斑叶螨）】刺吸式害虫，造成叶片失绿、黄化甚至枯焦。防治方法："
            "1. 农业防治：清除杂草，适当增加湿度；"
            "2. 生物防治：释放捕食螨（胡瓜钝绥螨等）；"
            "3. 化学防治：可选用阿维菌素、哒螨灵、联苯肼酯、乙螨唑等。"
            "高温干旱利于红蜘蛛爆发，注意药剂轮换使用避免产生抗药性。"
        ),
        "Tomato___Target_Spot": (
            "【番茄斑点病（靶斑病）】真菌性病害，叶片出现同心环纹状斑点。防治方法："
            "1. 农业防治：合理密植保持通风；"
            "2. 化学防治：发病初期喷施苯醚甲环唑、吡唑醚菌酯、嘧菌酯等。"
        ),
        "Tomato___Tomato_Yellow_Leaf_Curl_Virus": (
            "【番茄黄化曲叶病毒病（TYLCV）】由烟粉虱传播的毁灭性病毒病，植株矮化、叶片黄化卷曲。防治方法："
            "1. 物理防治：防虫网覆盖育苗和栽培（60目以上），银灰色地膜驱避粉虱；"
            "2. 化学防治：彻底防治传毒介体烟粉虱（B型/Q型），可选用噻虫嗪、螺虫乙酯、氟啶虫胺腈等；"
            "3. 农业防治：选用抗TYLCV品种，清除田间病株和杂草。"
            "\"防虫网+抗病品种+粉虱防治\"是防控TYLCV的关键三要素。"
        ),
        "Tomato___Tomato_mosaic_virus": (
            "【番茄花叶病毒病（ToMV）】接触传播的病毒病，叶片出现花叶斑驳。防治方法："
            "1. 农业防治：种子消毒（10%磷酸三钠浸种20分钟），农事操作前用肥皂洗手，及时拔除病株；"
            "2. 选用抗病品种。"
            "该病毒主要通过人手和农具接触传播，严格卫生操作是防控关键。"
        ),
        "Tomato___healthy": "番茄叶片状态健康，无需特殊处理。做好日常预防和病虫害监测工作。",
    }

    def __init__(self):
        """初始化病害识别服务（延迟加载模型）"""
        self.model = None
        self.class_names = []
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.transform = None
        self._init_transforms()

    def _init_transforms(self):
        """初始化图片预处理管道"""
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((self.IMG_SIZE, self.IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=self.MEAN, std=self.STD),
        ])

    def _load_class_names(self) -> List[str]:
        """
        加载病害类别名称

        返回：
            List[str]: 类别名称列表
        """
        class_file = Path(settings.disease_model_path).parent / "disease_classes.txt"
        if class_file.exists():
            with open(class_file, "r", encoding="utf-8") as f:
                names = [line.strip() for line in f if line.strip()]
            logger.info(f"从文件加载了 {len(names)} 个病害类别: {class_file}")
            return names
        else:
            # 回退：使用内置类别名
            names = list(self.DISEASE_CN_NAMES.keys())
            logger.warning(f"类别文件不存在，使用内置 {len(names)} 个类别")
            return names

    def _create_model(self) -> nn.Module:
        """
        创建 ResNet50 模型并替换分类头

        返回：
            nn.Module: 配置好的 ResNet50 模型
        """
        from torchvision.models import resnet50
        model = resnet50(weights=None)
        # 替换最后的全连接层，适配 39 个病害类别
        num_classes = len(self.class_names)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
        return model.to(self.device)

    def _load_model(self):
        """
        加载 ResNet50 病害分类模型

        功能：
        1. 加载类别名称
        2. 创建 ResNet50 模型
        3. 加载训练好的权重
        4. 设置为评估模式
        """
        logger.info("开始加载病害分类模型...")

        # 1. 加载类别名称
        self.class_names = self._load_class_names()
        logger.info(f"病害类别数量: {len(self.class_names)}")

        # 2. 创建模型
        self.model = self._create_model()

        # 3. 加载 checkpoint
        model_path = settings.disease_model_path
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"病害模型文件未找到: {model_path}")

        checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)

        # 提取模型权重（checkpoint 可能包含 optimizer、epoch 等信息）
        if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            state_dict = checkpoint["model_state_dict"]
            val_acc = checkpoint.get("val_acc", None)
            logger.info(f"从 checkpoint 加载模型权重（验证准确率: {val_acc}%）")
        else:
            state_dict = checkpoint
            logger.info("加载原始 state_dict")

        self.model.load_state_dict(state_dict)
        self.model.eval()
        logger.info(f"病害分类模型加载成功: {model_path}")

    def _preprocess_image(self, image_path: str) -> torch.Tensor:
        """
        预处理输入图片

        参数：
            image_path: 图片文件路径

        返回：
            torch.Tensor: 预处理后的图片张量 (1, 3, 224, 224)
        """
        _ensure_cv2()
        # 读取图片（OpenCV 读取为 BGR）
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"无法读取图片: {image_path}")
        # BGR -> RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # 应用预处理
        img_tensor = self.transform(img)
        # 添加 batch 维度
        img_tensor = img_tensor.unsqueeze(0)
        return img_tensor.to(self.device)

    def _get_disease_prediction(self, probs: torch.Tensor, top_k: int = 5) -> List[DiseasePrediction]:
        """
        从概率分布中解析 Top-K 预测结果

        参数：
            probs: Softmax 后的概率分布 (1, num_classes)
            top_k: 返回前 K 个结果

        返回：
            List[DiseasePrediction]: 预测结果列表
        """
        topk_probs, topk_indices = torch.topk(probs, top_k, dim=1)
        topk_probs = topk_probs[0].cpu().tolist()
        topk_indices = topk_indices[0].cpu().tolist()

        predictions = []
        for idx, prob in zip(topk_indices, topk_probs):
            class_name = self.class_names[idx]
            # 解析作物和病害名称（格式：Crop___Disease）
            parts = class_name.split("___", 1)
            crop = parts[0] if len(parts) > 0 else ""
            disease = parts[1] if len(parts) > 1 else class_name
            chinese_name = self.DISEASE_CN_NAMES.get(class_name, class_name)

            predictions.append(DiseasePrediction(
                class_id=idx,
                class_name=class_name,
                crop=crop,
                disease=disease,
                chinese_name=chinese_name,
                confidence=round(prob, 4),
                treatment_advice=self.DISEASE_ADVICE.get(class_name, "请结合当地实际情况，采取综合防治措施。建议咨询当地农技部门获取更精准的防治方案。")
            ))

        return predictions

    def classify_single_image(self,
                               image_path: str,
                               user_id: Optional[str] = None,
                               model_name: str = "resnet50-disease",
                               minio_svc=None) -> DiseaseResult:
        """
        单图病害分类

        参数：
            image_path: 图片文件路径
            user_id: 用户 ID（可选）
            model_name: 模型名称
            minio_svc: MinIO 服务实例（可选）

        返回：
            DiseaseResult: 病害分类结果
        """
        start_time = time.time()

        # 延迟加载模型
        if self.model is None:
            self._load_model()

        detection_id = str(uuid.uuid4())

        # 预处理图片
        img_tensor = self._preprocess_image(image_path)

        # 前向推理
        with torch.no_grad():
            output = self.model(img_tensor)
            probs = torch.softmax(output, dim=1)

        # 解析预测结果
        predictions = self._get_disease_prediction(probs, top_k=5)
        best_prediction = predictions[0]

        # 读取图片用于上传
        with open(image_path, 'rb') as f:
            original_image_bytes = f.read()

        # 上传图片到 MinIO
        minio = minio_svc if minio_svc is not None else minio_service
        original_object_name = minio.upload_image_bytes(
            original_image_bytes,
            os.path.basename(image_path)
        )
        original_image_key = f"uploads/{original_object_name}"

        # 计算耗时
        detection_time = time.time() - start_time

        # 构建图片 URL（相对路径，由 Nginx 反向代理）
        if minio.is_available:
            image_url = (
                f"/api/disease/files/"
                f"agri-pest-original/{original_object_name}"
            )
        else:
            image_url = (
                f"/static/uploads/"
                f"{original_object_name}"
            )

        # 保存检测记录到数据库
        self._save_to_database(
            user_id=user_id,
            detection_id=detection_id,
            model_name=model_name,
            detection_time=detection_time,
            original_image_key=original_image_key,
            best_prediction=best_prediction,
        )

        return DiseaseResult(
            detection_id=detection_id,
            image_url=image_url,
            result_image_url=image_url,  # 分类不需要标注，返回原图
            prediction=best_prediction,
            top5=predictions,
            detection_time=round(detection_time, 3),
            model_name=model_name,
            created_at=datetime.now(),
        )

    def _save_to_database(self,
                          user_id: Optional[str],
                          detection_id: str,
                          model_name: str,
                          detection_time: float,
                          original_image_key: str,
                          best_prediction: DiseasePrediction):
        """
        保存病害检测记录到数据库
        """
        try:
            db = next(get_db())
            record = DetectionRecord(
                id=detection_id,
                user_id=user_id,
                type="disease",
                status="completed",
                model_name=model_name,
                model_version="1.0.0",
                total_objects=1,
                detection_time=detection_time,
                original_image_key=original_image_key,
                result_image_key=original_image_key,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            logger.info(
                f"病害检测记录已保存: {detection_id} "
                f"[{best_prediction.crop}] {best_prediction.chinese_name} "
                f"置信度: {best_prediction.confidence}"
            )

        except Exception as e:
            logger.error(f"保存病害检测记录失败: {str(e)}")
            try:
                db.rollback()
            except:
                pass


# =============================================================================
# 全局病害识别服务实例
# =============================================================================
disease_service = DiseaseService()
