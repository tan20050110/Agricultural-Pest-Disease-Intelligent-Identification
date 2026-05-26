# 后端服务

## 快速启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
py -m uvicorn test_backend:app --host 0.0.0.0 --port 8000 --reload
```

## 模型配置

将训练好的 YOLO 模型文件命名为 `best.pt`，放入 `models/` 目录。

## API 文档

访问 http://localhost:8000/docs 查看完整 API 文档。

## 目录结构

```
backend/
├── app/              # 完整应用模块（需要Docker）
├── data/             # JSON数据库存储
├── models/           # YOLO模型文件
├── static/           # 静态文件（上传/结果）
├── test_backend.py   # 简化版后端（推荐使用）
├── main.py           # 完整版后端入口
└── requirements.txt  # Python依赖
```
