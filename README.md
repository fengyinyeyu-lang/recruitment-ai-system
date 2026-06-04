# 💼 招聘数据智能分析系统

基于拉勾网 29,500 条真实招聘数据，集成数据清洗、可视化分析、机器学习与大模型智能交互的一站式招聘市场洞察平台。

## 📋 系统功能模块

| 模块 | 功能描述 | 核心技术 |
|---|---|---|
| 📥 数据爬取 | 八爪鱼采集器采集多平台招聘数据 | 八爪鱼采集器 |
| 🧹 数据预处理 | 薪资解析、经验/学历标准化、缺失值处理 | Pandas, NumPy |
| 📊 数据可视化 | 薪资分布、城市对比、学历门槛、经验关联等 | ECharts, Matplotlib |
| ☁️ 岗位词云 | NLP 分词提取技能热词，生成词云画像 | Jieba, WordCloud |
| 🧠 机器学习 | KMeans 聚类 + Embedding 神经网络分类 | Scikit-learn, PyTorch, DashScope Embedding |
| 🤖 AI 智能客服 | 基于通义千问大模型的定制化求职建议 | DashScope API (qwen-turbo) |
| 🧮 薪资预测分析 | 基于RandomForest回归模型预测岗位薪资 | Scikit-learn, Label Encoding |
| 📜 对话历史管理 | 保存/搜索/浏览AI对话历史记录 | SQLAlchemy, SQLite |
| 🏢 企业深度画像 | 分析企业招聘规模、薪资、热门岗位 | Pandas, ECharts |
| 📋 分析报告导出 | 一键生成HTML格式招聘分析报告 | HTML Template |
| 🔐 用户系统 | 登录注册、会话管理、JWT认证 | FastAPI, Vue 3 |

## 🚀 快速开始

### 1. 环境准备

```bash
# 创建 Conda 虚拟环境
conda create -n recruitment python=3.11
conda activate recruitment

# 安装后端依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
```

### 2. 配置 API Key

在系统环境变量中设置阿里云百炼 API Key：

```
变量名: DASHSCOPE_API_KEY
变量值: 你的API Key
```

> 获取方式：登录 [阿里云百炼控制台](https://bailian.console.aliyun.com/) → API Key 管理 → 创建

### 3. 启动系统

**启动后端服务（FastAPI）：**
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**启动前端服务（Vue 3）：**
```bash
cd frontend
npm run dev
```

访问 http://localhost:3000 即可使用。

### 4. 默认账号

| 用户名 | 密码 |
|---|---|
| admin | 123456 |

## 📁 项目结构

```
recruitment_ai_system/
├── data/                           # 数据存储目录
│   ├── raw/                        # 原始采集数据
│   ├── processed/                  # 清洗后高质量数据
│   ├── text_features/              # NLP Embedding 特征缓存
│   └── users.json                  # 用户数据
├── models/                         # 训练好的模型文件
├── notebooks/                      # Jupyter Notebook 实验目录
├── src/                            # 核心业务逻辑（前后端共用）
│   ├── data_pipeline/              # 数据预处理模块
│   │   ├── cleaner.py              # 数据清洗
│   │   └── nlp_processor.py        # NLP 文本处理 + Embedding 向量化
│   ├── visualization/              # 可视化模块
│   │   └── visualization.py        # 图表绘制
│   ├── ml_engine/                  # 机器学习模块
│   │   ├── cluster.py              # KMeans 聚类
│   │   └── classifier.py           # 神经网络分类器 (PyTorch MLP)
│   └── llm_service/                # AI 智能交互模块
│       ├── chat_api.py             # 大模型 API 封装
│       └── prompts.py              # 提示词模板
├── backend/                        # FastAPI 后端服务
│   ├── main.py                     # 后端主入口
│   ├── config.py                   # 配置管理
│   ├── dependencies.py             # 依赖注入
│   ├── routers/                    # API 路由
│   │   ├── auth.py                 # 认证接口
│   │   ├── data.py                 # 数据查询接口
│   │   ├── visualization.py        # 可视化接口
│   │   ├── ml.py                   # 机器学习接口
│   │   └── ai.py                   # AI 助手接口
│   └── schemas/                    # Pydantic 模型定义
├── frontend/                       # Vue 3 前端应用
│   ├── src/
│   │   ├── views/                  # 页面组件
│   │   ├── layouts/                # 布局组件
│   │   ├── api/                    # API 封装
│   │   ├── stores/                 # Pinia 状态管理
│   │   └── router/                 # 路由配置
│   ├── vite.config.js              # Vite 配置
│   └── package.json                # 前端依赖
├── app/                            # 旧版 Streamlit 应用（已迁移）
├── config/                         # 配置文件
│   ├── config.yaml                 # 项目配置
│   └── .env.example                # 环境变量模板
├── requirements.txt                # 后端依赖清单
└── README.md                       # 本文件
```

## 🛠️ 技术栈

| 分类 | 技术 | 版本 |
|---|---|---|
| 前端框架 | Vue 3 | 3.4+ |
| 前端 UI | Element Plus | 2.8+ |
| 前端图表 | ECharts | 5.5+ |
| 前端状态 | Pinia | 2.1+ |
| 后端框架 | FastAPI | 0.115+ |
| 数据处理 | Pandas, NumPy | 2.2+, 1.26+ |
| 可视化 | Matplotlib, Seaborn | 3.8+, 0.13+ |
| NLP | Jieba 分词, DashScope Embedding | - |
| 机器学习 | Scikit-learn, PyTorch | 1.4+, 2.2+ |
| 大模型 | 阿里云 DashScope (qwen-turbo) | - |
| 数据库 | SQLAlchemy + SQLite | 2.0+ |
| 认证 | JWT | PyJWT |

## ✨ 高级功能

### 🧮 薪资预测分析
基于 **RandomForest 回归模型**，利用城市、学历、工作经验、岗位类别、行业领域和公司规模等特征，智能预测岗位的合理薪资范围。

### 📜 AI 对话历史管理
保存每次与 AI 助手的对话记录到数据库，支持按关键词搜索和时间排序浏览。

### 🏢 企业深度画像分析
选择任意企业，自动分析其招聘画像，包括热门岗位分布、城市布局、学历门槛、薪资水平等。

### 📋 智能分析报告导出
一键生成包含核心指标、薪资排行、岗位需求、学历分布的 **HTML 专业报告**。

## 🔧 API 文档

启动后端服务后，访问 Swagger UI：
- http://localhost:8000/docs

## 📝 开发说明

### 后端开发
```bash
# 开发模式（自动重载）
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端开发
```bash
# 开发模式（热更新）
cd frontend
npm run dev

# 生产构建
npm run build
```

### 代码规范
- 后端：遵循 PEP 8 规范
- 前端：使用 ESLint + Prettier
