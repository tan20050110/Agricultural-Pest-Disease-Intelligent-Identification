# -*- coding: utf-8 -*-
# =============================================================================
# AI 问答 API 路由模块
# =============================================================================
import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, Form, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.models.database import get_db, AIQARecord

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/qa", tags=["qa"])


class QAResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


# 农业病虫害知识库
PEST_KNOWLEDGE = {
    "稻瘟病": "稻瘟病是水稻最严重的病害之一。防治方法：1.选用抗病品种；2.合理施肥，避免过量氮肥；3.分蘖盛期和抽穗期喷药，可使用三环唑、异稻瘟净等药剂；4.及时处理病稻草。",
    "蚜虫": "蚜虫是常见的刺吸式害虫。防治方法：1.生物防治，引入瓢虫、蚜茧蜂等天敌；2.使用黄色粘虫板诱杀；3.使用吡虫啉、啶虫脒等药剂喷雾；4.清除田间杂草减少虫源。",
    "蝗虫": "蝗虫是农业重大害虫。防治方法：1.生态控制，保护天敌；2.使用马拉硫磷、敌敌畏等药剂进行喷雾；3.蝗蝻期集中防治效果最好；4.加强监测预警。",
    "二化螟": "二化螟是水稻主要钻蛀性害虫。防治方法：1.越冬期灌水灭蛹；2.灯光诱杀成虫；3.卵孵高峰期使用杀虫双、阿维菌素等药剂；4.保护寄生蜂等天敌。",
    "玉米螟": "玉米螟是玉米主要钻蛀性害虫。防治方法：1.处理秸秆消灭越冬虫源；2.心叶期使用辛硫磷颗粒剂灌心；3.释放赤眼蜂进行生物防治；4.选用抗虫品种。",
    "粘虫": "粘虫是暴食性迁飞害虫。防治方法：1.糖醋液诱杀成虫；2.幼虫3龄前使用高效氯氰菊酯等药剂；3.利用黑光灯诱杀；4.加强预测预报。",
    "稻纵卷叶螟": "稻纵卷叶螟是水稻重要迁飞性害虫。防治方法：1.合理施肥避免偏施氮肥；2.保护寄生蜂天敌；3.卵孵高峰期使用阿维菌素、甲维盐等药剂；4.成虫盛发期使用灯光诱杀。",
    "小麦锈病": "小麦锈病分为条锈、叶锈和秆锈。防治方法：1.选用抗病品种；2.合理密植，加强田间管理；3.发病初期使用三唑酮、戊唑醇等药剂；4.适期播种避免过密。",
    "稻飞虱": "稻飞虱是水稻重要刺吸式害虫。防治方法：1.选用抗性品种；2.合理施肥控制群体密度；3.使用吡虫啉、噻虫嗪等药剂；4.保护天敌如蜘蛛和寄生蜂。",
}


def get_ai_response(question: str) -> str:
    """根据问题关键词匹配知识库"""
    question_lower = question.lower()
    for keyword, answer in PEST_KNOWLEDGE.items():
        if keyword in question or keyword in question_lower:
            return answer
    
    # 常见问题的通用回答
    if "防治" in question or "怎么办" in question or "方法" in question:
        return "针对您的问题，建议：1.首先确诊病虫害类型；2.选用登记的农药品种；3.把握最佳防治时期；4.轮换用药防止抗药性。建议上传图片使用本平台的检测功能进行确诊。"
    
    if "症状" in question or "表现" in question:
        return "不同病虫害有不同症状表现。建议您上传作物图片到本平台的检测功能，AI将自动识别病虫害类型并提供详细信息。"
    
    if "施肥" in question or "肥料" in question:
        return "施肥建议：1.根据土壤检测结果合理施肥；2.有机肥与化肥配合使用；3.注意氮磷钾比例平衡；4.不同作物不同生育期施肥策略不同。"
    
    return "感谢您的提问！建议您使用本平台的虫害检测或病害识别功能，上传作物图片进行AI智能诊断。如需更专业的建议，请咨询当地农业技术推广部门。"


@router.post("/ask", response_model=QAResponse)
async def ask_question(
    question: str = Form(..., description="用户问题"),
    user_id: str = Form(None),
):
    """
    AI 问答接口
    
    功能：
    - 接收用户问题
    - 基于知识库匹配回答
    - 保存问答记录到数据库
    
    参数：
        question: 用户问题
        user_id: 用户 ID（可选）
    
    返回：
        QAResponse: 包含回答的响应
    """
    try:
        if not question or not question.strip():
            return {
                "success": False,
                "message": "请输入问题",
                "data": None
            }
        
        # 获取AI回答
        answer = get_ai_response(question.strip())
        
        # 保存问答记录到数据库
        try:
            db = next(get_db())
            record = AIQARecord(
                id=str(uuid.uuid4()),
                user_id=user_id,
                question=question.strip(),
                answer=answer,
                model_name="knowledge-base",
                status="completed",
                created_at=datetime.now()
            )
            db.add(record)
            db.commit()
        except Exception as e:
            logger.warning(f"保存问答记录失败: {e}")
        
        return {
            "success": True,
            "message": "回答成功",
            "data": {
                "question": question.strip(),
                "answer": answer,
                "created_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"AI问答异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=QAResponse)
async def get_qa_history(
    user_id: str = None,
    limit: int = 20
):
    """
    获取问答历史记录
    
    参数：
        user_id: 用户 ID（可选）
        limit: 返回数量限制
    """
    try:
        db = next(get_db())
        query = db.query(AIQARecord).order_by(AIQARecord.created_at.desc())
        if user_id:
            query = query.filter(AIQARecord.user_id == user_id)
        
        records = query.limit(limit).all()
        
        history = []
        for r in records:
            history.append({
                "id": str(r.id),
                "question": r.question,
                "answer": r.answer,
                "created_at": r.created_at.isoformat() if r.created_at else ""
            })
        
        return {
            "success": True,
            "message": "获取成功",
            "data": {"records": history, "total": len(history)}
        }
        
    except Exception as e:
        logger.error(f"获取问答历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
