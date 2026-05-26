# 🚀 添加训练好的YOLO模型 - 完整步骤教程

## 📋 目录
1. [准备工作](#1-准备工作)
2. [模型文件放置](#2-模型文件放置)
3. [配置类别映射](#3-配置类别映射)
4. [安装依赖](#4-安装依赖)
5. [启动测试](#5-启动测试)
6. [常见问题](#6-常见问题)

---

## 1️⃣ 准备工作

### 1.1 确保您有训练好的模型文件
您需要一个 `.pt` 格式的YOLO模型文件，通常命名为：
- `best.pt`（推荐，训练过程中保存的最佳模型）
- `last.pt`（训练结束时的最后一个模型）

### 1.2 确认模型类别信息
在训练模型时，您应该有一个 `data.yaml` 文件，里面记录了类别名称，例如：
```yaml
names:
  0: rice_blast
  1: wheat_rust
  2: aphid
  3: locust
  4: barnyard_grass
  5: nutrient_deficiency
```

请保存好这些类别信息！

---

## 2️⃣ 模型文件放置

### 步骤 2.1: 找到模型目录
模型目录位置：`backend/models/`

```
rsod-web-platform/
└── backend/
    └── models/          ← 把模型文件放在这里
        ├── .gitkeep
        └── yolo11n.pt  (已有的预训练模型)
```

### 步骤 2.2: 复制模型文件
将您训练好的模型文件复制到 `backend/models/` 目录，并重命名为 `best.pt`

```bash
# 示例（Windows PowerShell）
copy "您的模型路径\best.pt" "backend\models\best.pt"
```

**重要：** 模型文件名必须是 `best.pt`（这是默认配置）

---

## 3️⃣ 配置类别映射

### 步骤 3.1: 打开配置文件
编辑文件：`backend/simple_backend.py`

### 步骤 3.2: 修改类别配置
找到以下代码段（大约在第47-64行）：

```python
# 病虫害类别映射（根据您的模型训练类别修改）
CLASS_NAMES = {
    0: "rice_blast",
    1: "wheat_rust",
    2: "aphid",
    3: "locust",
    4: "barnyard_grass",
    5: "nutrient_deficiency"
}

CLASS_NAMES_CN = {
    0: "稻瘟病",
    1: "小麦锈病",
    2: "蚜虫",
    3: "蝗虫",
    4: "稗草",
    5: "缺素症状"
}
```

### 步骤 3.3: 根据您的模型修改
根据您的 `data.yaml` 文件内容，修改上述两个字典：

**示例：** 如果您的模型有3个类别：
```yaml
names:
  0: apple_scab
  1: apple_black_rot
  2: cedar_apple_rust
```

则修改为：
```python
CLASS_NAMES = {
    0: "apple_scab",
    1: "apple_black_rot",
    2: "cedar_apple_rust"
}

CLASS_NAMES_CN = {
    0: "苹果黑星病",
    1: "苹果黑斑病",
    2: "雪松苹果锈病"
}
```

---

## 4️⃣ 安装依赖

### 4.1 检查并安装所需Python包
打开终端，进入 `backend` 目录：

```bash
cd backend
```

### 4.2 安装ultralytics和opencv
```bash
pip install ultralytics opencv-python
```

如果安装速度慢，可以使用国内镜像：
```bash
pip install ultralytics opencv-python -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 5️⃣ 启动测试

### 5.1 停止旧服务（如果正在运行）
在之前运行后端的终端按 `Ctrl + C` 停止服务

### 5.2 重新启动后端服务
```bash
cd backend
py -3 simple_backend.py
```

### 5.3 观察启动日志
启动时应该看到：
```
============================================================
农业病虫害智能识别系统 - 简化版后端
============================================================

[DOC] API 文档地址: http://localhost:8000/docs
[WEB] 健康检查: http://localhost:8000/health

[MODEL] 正在加载模型...
✅ 模型加载成功: best.pt            ← 看到这行说明成功！

[RUN] 启动中...
```

### 5.4 测试检测功能
1. 打开前端：http://localhost:5173
2. 登录后上传一张病虫害图片
3. 查看检测结果是否正确

---

## 6️⃣ 常见问题

### ❓ Q1: 启动时提示"未找到模型文件"
**A:** 检查以下几点：
1. 模型文件确实在 `backend/models/` 目录
2. 文件名是 `best.pt`（小写）
3. 文件名没有多余的后缀（如 `best.pt.pt`）

### ❓ Q2: 提示"模型加载失败"
**A:** 可能原因：
1. PyTorch版本不兼容
2. 模型文件损坏
3. 缺少依赖包，重新运行：
   ```bash
   pip install ultralytics opencv-python torch torchvision
   ```

### ❓ Q3: 检测结果类别名称不对
**A:** 检查 `simple_backend.py` 中的 `CLASS_NAMES` 和 `CLASS_NAMES_CN` 配置是否与训练时的类别一致

### ❓ Q4: 如何更换其他模型？
**A:** 有两种方式：
1. 替换 `best.pt` 文件为新模型
2. 修改 `DEFAULT_MODEL` 变量（在 `simple_backend.py` 第43行）：
   ```python
   DEFAULT_MODEL = "your_model.pt"  # 修改为您的模型文件名
   ```

### ❓ Q5: 如何调整检测置信度阈值？
**A:** 在前端检测时可以设置，或者修改后端默认值（`simple_backend.py` 第274行）：
```python
confidence_threshold: float = Form(0.25)  # 修改这个值，0-1之间
```

---

## 🎉 完成！

现在您已经成功添加了自定义训练的YOLO模型！如果还有问题，请检查后端终端的错误日志。

---

## 📝 快速检查清单

在启动前，请确认：
- [ ] 模型文件 `best.pt` 已放在 `backend/models/` 目录
- [ ] `CLASS_NAMES` 和 `CLASS_NAMES_CN` 已配置正确
- [ ] `ultralytics` 和 `opencv-python` 已安装
- [ ] 使用 `py -3 simple_backend.py` 启动后端
