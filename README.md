# 农业病虫害智能识别系统

> 基于 YOLO 和 ResNet50 的深度学习农作物病虫害图像识别平台，支持虫害目标检测和病害分类识别，提供智能防治建议。

---

## 📋 目录

- [项目简介](#项目简介)
- [核心亮点](#核心亮点)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [添加自定义模型](#添加自定义模型)
- [项目结构](#项目结构)
- [API 文档](#api-文档)
- [部署说明](#部署说明)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

---

## 项目简介

**农业病虫害智能识别系统**是一个基于深度学习的农业图像识别平台，集成 YOLO 目标检测和 ResNet50 图像分类两大模型，实现对农作物虫害（102 类）和病害（39 类）的快速、准确识别，并提供智能防治建议。

### 应用场景

- 农田虫害现场拍照识别（YOLO 目标检测）
- 作物病害叶片拍照识别（ResNet50 分类）
- 农业技术推广与远程诊断
- 农作物健康监测与预警
- 病虫害防治决策支持
- 农业知识智能问答

---

## 核心亮点

| 亮点 | 说明 |
|------|------|
| 🚀 **双模型引擎** | YOLO 虫害目标检测 + ResNet50 病害分类识别，覆盖农业全场景 |
| 🎯 **多目标检测** | 支持 102 类农作物虫害同步识别，精准框选定位 |
| 🍎 **病害识别** | 基于 ResNet50 的 39 类作物病害分类，支持 Top-5 预测与防治建议 |
| 📊 **可视化展示** | 检测结果实时标注，支持框选、置信度展示和概率排名 |
| 📱 **友好界面** | Vue3 + Element Plus 现代化前端，操作直观 |
| 💬 **农技问答** | AI 智能问答系统，提供病虫害防治建议 |
| 👤 **用户认证** | 完整的注册 / 登录 / 忘记密码流程 |
| 🌍 **多语言支持** | 支持中文 / 英文切换 |
| 🎨 **主题切换** | 支持亮色 / 暗色 / 跟随系统主题 |
| 🔀 **双模式切换** | 自动检测环境，Docker 全栈 / 本地轻量无缝切换 |
| 📈 **检测历史** | 自动保存检测记录，支持回溯查看 |

---

## 技术栈

### 前端

| 技术 | 版本 | 说明 |
|------|------|------|
| Vue.js | 3.x | 前端框架 |
| Element Plus | 2.x | UI 组件库 |
| Vue Router | 4.x | 路由管理 |
| Pinia | 3.x | 状态管理 |
| Vue I18n | 9.x | 国际化 |
| Axios | 1.x | HTTP 客户端 |
| ECharts | 5.x | 数据可视化 |
| Vite | 8.x | 构建工具 |

### 后端

| 技术 | 版本 | 说明 |
|------|------|------|
| Python | 3.10+ | 编程语言 |
| FastAPI | 0.104+ | Web 框架 |
| Uvicorn | 0.24+ | ASGI 服务器 |
| SQLAlchemy | 2.x | ORM 框架 |
| Ultralytics YOLO | 8.x | 虫害目标检测模型（支持 CUDA） |
| PyTorch | 2.x | 深度学习框架（YOLO + ResNet50） |
| ResNet50 | - | 病害图像分类模型（PlantVillage 数据集） |
| PostgreSQL | 16 | 数据库（Docker 模式） |
| MinIO | latest | 对象存储（Docker 模式） |
| Redis | latest | 缓存（Docker 模式） |
| SQLite | - | 数据库（本地模式，零配置） |

> **双模式架构**：系统启动时自动检测环境——有 PostgreSQL 则用全栈 Docker 模式，否则自动降级为 SQLite + 本地文件存储，无需手动切换配置。

---

## 快速开始

### 环境要求

- **Docker Desktop**（必需，用于运行所有服务）
- **浏览器**（Chrome、Edge、Firefox、Safari 等现代浏览器）
- **摄像头**（可选，用于实时检测功能）

> 💡 **提示**：推荐使用 Chrome 或 Edge 浏览器以获得最佳体验。

---

### Docker 全栈启动（推荐）

这是最简单、最快速的使用方式，一键启动所有服务：

```bash
# 在项目根目录执行
docker-compose up -d
```

**自动启动的服务：**

| 服务 | 端口 | 说明 |
|------|------|------|
| PostgreSQL 16 | 5432 | 关系数据库 |
| MinIO | 9000 / 9001 | 对象存储 / 管理控制台 |
| Redis | 6379 | 缓存服务 |
| 后端 (FastAPI) | 8000 | API 服务 |
| 前端 (Nginx) | 80 | Web 界面 |

---

### 常用 Docker 命令

```bash
# 启动所有服务（首次使用或重启后）
docker-compose up -d

# 查看所有容器状态
docker-compose ps

# 查看后端日志（实时监控）
docker-compose logs -f backend

# 查看前端日志
docker-compose logs -f frontend

# 停止所有服务
docker-compose down

# 重启所有服务
docker-compose restart

# 重启单个服务
docker-compose restart backend

# 进入后端容器（调试用）
docker exec -it rsod-backend bash

# 重新构建并启动（代码更新后使用）
docker-compose up -d --build
```

---

### 登录使用

1. 打开浏览器访问：**http://localhost/**
2. 点击"注册"创建新账号，或使用测试账号：
   - **用户名**：`testuser`
   - **密码**：`Docker1234`
3. 登录后即可使用所有功能

---

### 服务地址汇总

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端页面 | http://localhost | 主页面（Docker 模式） |
| 后端 API 文档 (Swagger) | http://localhost:8000/docs | 完整的交互式 API 文档 |
| 后端健康检查 | http://localhost:8000/health | 服务健康状态 |
| MinIO 控制台 | http://localhost:9001 | 对象存储管理（用户名：admin，密码：minio_password） |

---

### 本地开发模式（可选）

如果你想进行开发或修改代码，可以选择本地模式：

```bash
# 1. 安装后端依赖
cd backend
pip install -r requirements.txt

# 2. 启动后端（自动检测并降级为 SQLite）
python main.py

# 3. 新终端启动前端
cd frontend
npm install
npm run dev
```

本地模式会使用 SQLite 数据库而非 PostgreSQL，适合开发调试。

---

## 页面功能

| 页面 | 路由 | 功能说明 |
|------|------|----------|
| 登录 | `/login` | 用户登录，支持记住我功能 |
| 注册 | `/register` | 新用户注册（用户名、邮箱、密码） |
| 忘记密码 | `/forgot-password` | 密码找回（通过邮箱） |
| 虫害检测 | `/detection` | YOLO 目标检测，识别 102 类农业害虫，支持单图、批量、图片夹、视频检测 |
| 病害识别 | `/disease` | ResNet50 分类，识别 39 类作物病害，显示 Top-5 预测结果及防治建议 |
| 摄像头检测 | `/camera` | 实时摄像头目标检测，实时显示 FPS、检测耗时和目标数量 |
| 历史记录 | `/history` | 查看检测历史与详情，支持筛选和删除 |
| AI 问答 | `/qa` | 智能农业知识问答，基于病虫害知识库提供智能回答 |
| 目标库 | `/targets` | 浏览可检测的病虫草害类别，展示 9 大类 102 种害虫信息 |
| 个人中心 | `/profile` | 用户信息管理、统计数据展示 |
| 系统设置 | `/settings` | 主题切换（亮色/暗色/跟随系统）、语言设置（中/英文）、账户设置 |

### 摄像头检测功能

摄像头实时检测功能支持：

- ✅ **实时视频流**：通过摄像头实时获取画面
- ✅ **实时检测**：YOLO 模型实时分析视频帧
- ✅ **FPS 显示**：实时显示检测帧率
- ✅ **目标统计**：显示当前检测到的目标数量
- ✅ **可视化标注**：在视频画面上实时绘制检测框
- ✅ **暂停/恢复**：支持暂停和恢复检测
- ✅ **权限引导**：详细的摄像头权限设置指引

**首次使用摄像头时的权限设置指引**：

当浏览器提示摄像头权限请求时，请选择"允许"。如果不小心拒绝了权限，系统会显示详细的操作指引，帮助您在浏览器设置中开启摄像头权限。

---

## 添加自定义模型

系统支持两类 AI 模型：**YOLO 目标检测**（虫害）和 **ResNet50 分类**（病害）。你可以添加自己训练的模型。

### 添加 YOLO 虫害检测模型

如果你有自己训练的 YOLO 模型（`.pt` 文件），按以下步骤添加：

#### 1. 放置模型文件

将模型文件放入 `backend/models/` 目录：

```
backend/models/
├── yolo11n.pt          ← 默认通用模型
└── my_custom_model.pt  ← 你的自定义模型
```

#### 2. 修改配置

编辑 `backend/.env`，修改模型路径：

```ini
YOLO_MODEL_PATH=models/my_custom_model.pt
```

#### 3. 更新类别名称（可选）

如果你的模型使用不同的类别标签，编辑 `backend/app/services/detection_service.py` 中的 `_init_class_names` 和 `get_class_chinese_name` 方法，添加对应的类别映射。

### 添加 ResNet50 病害分类模型

#### 1. 放置模型和类别文件

```
backend/models/
├── resnet50_disease.pth     ← 训练好的 ResNet50 权重
└── disease_classes.txt      ← 类别名称列表（每行一个类别）
```

#### 2. 修改配置

编辑 `backend/.env`，设置模型路径：

```ini
RESNET_MODEL_PATH=models/resnet50_disease.pth
```

#### 3. 更新类别名称

编辑 `backend/app/services/disease_service.py`，修改 `DISEASE_CN_NAMES` 字典添加中文类别映射。

### 重启后端

后端以 `reload=True` 模式运行，修改配置后会自动重启。刷新前端页面即可使用新模型。

---

## 项目结构

```
rsod-web-platform/
├── backend/                              # 后端代码
│   ├── app/                              #   应用模块
│   │   ├── api/                          #     API 路由
│   │   │   ├── auth.py                   #       认证接口（注册/登录/忘记密码）
│   │   │   ├── detection.py              #       虫害检测接口（单图/历史/文件代理）
│   │   │   ├── disease.py                #       病害识别接口（单图分类/类别列表）
│   │   │   └── model.py                  #       模型管理接口
│   │   ├── models/                       #     数据模型
│   │   │   ├── database.py               #       ORM 模型（自动适配 PostgreSQL/SQLite）
│   │   │   └── schemas.py                #       Pydantic 请求/响应模型
│   │   ├── services/                     #     业务服务
│   │   │   ├── auth_service.py           #       认证逻辑
│   │   │   ├── simple_auth_service.py    #       本地模式认证（SQLite）
│   │   │   ├── detection_service.py      #       YOLO 虫害检测逻辑
│   │   │   ├── disease_service.py        #       ResNet50 病害分类逻辑
│   │   │   ├── redis_service.py          #       Redis 缓存（可选）
│   │   │   └── minio_service.py          #       文件存储（可选）
│   │   ├── utils/                        #     工具函数
│   │   │   └── file_utils.py             #       文件上传/目录管理
│   │   └── config.py                     #     全局配置（环境变量）
│   ├── data/                             #   SQLite 数据库文件（本地模式）
│   ├── models/                           #   AI 模型文件
│   │   ├── best.pt                        #     YOLO 虫害检测模型
│   │   ├── yolo11n.pt                     #     YOLO11 Nano 通用回退模型
│   │   ├── resnet50_disease.pth           #     ResNet50 病害分类权重
│   │   ├── disease_classes.txt            #     病害类别名称列表（39 类）
│   │   └── model_info.json               #     本地模型版本信息
│   ├── static/                           #   静态文件
│   │   ├── uploads/                      #     用户上传的原始图片
│   │   └── results/                      #     检测结果图片
│   ├── main.py                           #   后端入口
│   ├── .env                              #   环境配置
│   └── requirements.txt                  #   Python 依赖
├── frontend/                             # 前端代码
│   ├── src/
│   │   ├── api/                          #   API 封装
│   │   │   └── auth.js                   #     认证 API
│   │   ├── components/                   #   公共组件
│   │   │   ├── Header.vue                #     顶部导航栏
│   │   │   └── Sidebar.vue               #     侧边栏（作物选择）
│   │   ├── views/                        #   页面视图
│   │   │   ├── LoginPage.vue             #     登录页
│   │   │   ├── RegisterPage.vue          #     注册页
│   │   │   ├── ForgotPasswordPage.vue    #     忘记密码页
│   │   │   ├── DetectionPage.vue         #     虫害检测页
│   │   │   ├── DiseasePage.vue           #     病害识别页
│   │   │   ├── HistoryPage.vue           #     历史记录页
│   │   │   ├── QAPage.vue                #     AI 问答页
│   │   │   ├── TargetsPage.vue           #     目标类别库
│   │   │   ├── ProfilePage.vue           #     个人中心
│   │   │   └── Settings.vue              #     系统设置
│   │   ├── stores/                       #   Pinia 状态管理
│   │   │   ├── index.js                  #     主 Store
│   │   │   └── user.js                   #     用户状态
│   │   ├── router/                       #   Vue Router 路由
│   │   │   └── index.js                  #     路由配置 + 导航守卫
│   │   ├── locales/                      #   国际化
│   │   │   ├── zh-CN.js                  #     中文
│   │   │   └── en-US.js                  #     英文
│   │   ├── utils/                        #   工具函数
│   │   ├── App.vue                       #   根组件
│   │   ├── main.js                       #   应用入口
│   │   └── style.css                     #   全局样式与 CSS 变量
│   ├── package.json
│   └── vite.config.js
├── storage/                              # Docker 持久化存储（可选）
├── docker-compose.yml                    # Docker Compose 完整部署配置
└── README.md
```

---

## API 文档

> 💡 **提示**：完整的交互式 API 文档请访问 http://localhost:8000/docs

### 认证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| POST | `/api/auth/forgot-password` | 忘记密码 |
| POST | `/api/auth/reset-password` | 重置密码 |
| GET | `/api/auth/me` | 获取当前用户信息（需认证） |

### 虫害检测接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/detection/single` | 单图虫害检测（multipart/form-data） |
| GET | `/api/detection/history` | 获取检测历史记录 |
| GET | `/api/detection/{id}` | 获取单条检测详情 |
| DELETE | `/api/detection/{id}` | 删除检测记录 |
| GET | `/api/detection/targets/list` | 获取可检测虫害类别列表（102 类） |
| GET | `/api/detection/files/{bucket}/{filename}` | 文件代理（MinIO 模式） |

### 病害识别接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/disease/single` | 单图病害分类（multipart/form-data），返回 Top-5 预测 |
| GET | `/api/disease/targets/list` | 获取病害类别列表（39 类） |
| GET | `/api/disease/files/{bucket}/{filename}` | 文件代理（MinIO 模式） |

### 摄像头检测接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/camera/start` | 启动摄像头检测服务 |
| POST | `/api/camera/detect` | 发送视频帧进行检测（Base64 编码） |
| POST | `/api/camera/pause` | 暂停检测 |
| POST | `/api/camera/resume` | 恢复检测 |
| POST | `/api/camera/stop` | 停止检测服务 |

### AI 问答接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/qa/ask` | 提交问答问题 |
| GET | `/api/qa/history` | 获取问答历史记录 |
| GET | `/api/qa/targets/list` | 获取知识库可问答的病虫害类别 |

### 用户接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/user/profile` | 获取用户信息 |
| PUT | `/api/user/profile` | 更新用户信息 |
| PUT | `/api/user/password` | 修改密码 |

### 模型管理接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/model/list` | 获取可用模型列表 |
| GET | `/api/model/current` | 获取当前加载的模型信息 |
| POST | `/api/model/reload` | 重新加载模型 |

### 系统接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 应用基本信息 |
| GET | `/health` | 健康检查（数据库 / Redis / MinIO） |

---

## 部署说明

### 双模式架构

系统采用**自动环境检测**机制，无需手动切换配置：

```
启动 → 尝试连接 PostgreSQL
        ├── 成功 → Docker 全栈模式（PostgreSQL + MinIO + Redis）
        └── 失败 → 本地轻量模式（SQLite + 本地文件存储）
```

| 特性 | 本地模式 | Docker 模式 |
|------|----------|------------|
| 数据库 | SQLite（自动创建） | PostgreSQL 16 |
| 文件存储 | `static/uploads/` `static/results/` | MinIO 对象存储 |
| 缓存 | 降级跳过 | Redis |
| 适用场景 | 开发、演示、单机 | 生产、团队协作 |
| 启动命令 | `python main.py` | `docker-compose up -d` |

### 环境变量参考

在 `backend/.env` 中配置，核心变量：

```ini
# 应用配置
APP_NAME=农业病虫害智能识别系统
APP_VERSION=1.0.0
DEBUG=true
HOST=0.0.0.0
PORT=8000

# 数据库（Docker 模式）
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=agri_user
DB_PASSWORD=agri_password
DB_DATABASE=agri_platform

# MinIO（Docker 模式）
MINIO_HOST=localhost
MINIO_PORT=9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=minio_password

# Redis（Docker 模式）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis_password

# YOLO 虫害检测模型
YOLO_MODEL_PATH=models/yolo11n.pt
CONFIDENCE_THRESHOLD=0.3
IOU_THRESHOLD=0.45

# ResNet50 病害分类模型
RESNET_MODEL_PATH=models/resnet50_disease.pth
```

---

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 常见问题与故障排查

### ❌ 摄像头无法访问

**问题**：点击"启动检测"后提示摄像头权限被拒绝

**解决方案**：
1. 在浏览器地址栏左侧点击锁定图标或摄像头图标
2. 在权限设置中选择"允许"摄像头访问
3. 点击页面上的"刷新并重试"按钮

**各浏览器设置位置**：
- **Chrome/Edge**：地址栏左侧锁定图标 → 摄像头 → 允许
- **Firefox**：地址栏左侧权限图标 → 摄像头 → 允许
- **Safari**：Safari 菜单 → 偏好设置 → 网站 → 摄像头

### ❌ Docker 容器启动失败

**问题**：`docker-compose up -d` 失败

**解决方案**：
```bash
# 1. 确保 Docker Desktop 正在运行
# 2. 查看详细错误信息
docker-compose logs

# 3. 重新构建镜像
docker-compose down
docker-compose up -d --build

# 4. 检查端口占用
netstat -ano | findstr "5432"  # 检查 PostgreSQL 端口
netstat -ano | findstr "6379"  # 检查 Redis 端口
```

### ❌ 检测结果不准确

**问题**：上传图片后检测结果为空或不准确

**原因说明**：
- 当前 YOLO 模型是通用预训练模型，不是专门针对农业害虫训练的
- 如需提高准确率，建议使用农业害虫数据集对模型进行微调

**改进方案**：
1. 收集农业害虫图片数据集
2. 使用 YOLO 训练自定义模型
3. 将训练好的模型替换 `backend/models/best.pt`

### ❌ 页面样式显示异常

**问题**：Element Plus 组件样式加载失败

**解决方案**：
```bash
# 清理浏览器缓存或使用无痕模式

# 如果使用本地开发模式，重新安装依赖
cd frontend
rm -rf node_modules
npm install
npm run dev
```

### ❌ 登录失败

**问题**：无法登录系统

**解决方案**：
1. 确保所有 Docker 容器都在运行：`docker-compose ps`
2. 清除浏览器缓存后重试
3. 注册新账号使用
4. 检查后端日志：`docker-compose logs backend`

---

## 🎯 使用技巧

### 1. **虫害检测最佳实践**
- 使用清晰、光线充足的照片
- 确保目标害虫在图片中清晰可见
- 批量检测时，同类害虫放在同一文件夹

### 2. **病害识别建议**
- 拍摄叶片正面，避免阴影遮挡
- 尽量包含病斑全貌，便于模型识别
- 结合 AI 问答获取防治建议

### 3. **摄像头检测**
- 确保环境光线充足
- 摄像头与目标保持适当距离
- 避免背景过于复杂

### 4. **AI 问答**
- 描述问题时尽量详细（作物种类、虫害部位、症状等）
- 可以同时咨询防治方法和用药建议

---

## 📞 技术支持

如果你遇到其他问题，可以：

1. 查看 **API 文档** http://localhost:8000/docs 了解接口详情
2. 查看 **后端日志** `docker-compose logs -f backend` 获取错误信息
3. 提交 Issue 或联系开发团队

---

## 许可证

本项目采用 MIT 许可证。
