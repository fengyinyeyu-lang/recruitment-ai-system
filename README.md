# 💼 招聘数据智能分析系统

基于拉勾网 29,500 条真实招聘数据，集成数据清洗、可视化分析、机器学习与大模型智能交互的一站式招聘市场洞察平台。

## 📋 系统功能模块

| 模块 | 功能描述 | 核心技术 |
|---|---|---|
| 📥 数据爬取 | 八爪鱼采集器采集多平台招聘数据 | 八爪鱼采集器 |
| 🧹 数据预处理 | 薪资解析、经验/学历标准化、缺失值处理 | Pandas, NumPy |
| 📊 数据可视化 | 薪资分布、城市对比、学历门槛、经验关联等 | Matplotlib, Seaborn |
| ☁️ 岗位词云 | NLP 分词提取技能热词，生成词云画像 | Jieba, WordCloud |
| 🧠 机器学习 | KMeans 聚类 + Embedding 神经网络分类 | Scikit-learn, PyTorch, DashScope Embedding |
| 🤖 AI 智能客服 | 基于通义千问大模型的定制化求职建议 | DashScope API (qwen-turbo) |
| 🔐 用户系统 | 登录注册、会话管理 | Streamlit, JSON |

## 🚀 快速开始

### 1. 环境准备

```bash
# 创建 Conda 虚拟环境
conda create -n nlp python=3.11
conda activate nlp

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 API Key

在系统环境变量中设置阿里云百炼 API Key：

```
变量名: DASHSCOPE_API_KEY
变量值: 你的API Key
```

> 获取方式：登录 [阿里云百炼控制台](https://bailian.console.aliyun.com/) → API Key 管理 → 创建

### 3. 启动系统

```bash
streamlit run app/main.py
```

访问 http://localhost:8501 即可使用。

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
├── src/                            # 核心后端逻辑
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
├── app/                            # Streamlit 前端
│   ├── main.py                     # 主入口
│   ├── components/                 # 页面组件
│   │   └── auth.py                 # 登录注册
│   └── pages/                      # 多页面路由
├── config/                         # 配置文件
│   ├── config.yaml                 # 项目配置
│   └── .env.example                # 环境变量模板
├── requirements.txt                # 依赖清单
└── README.md                       # 本文件
```

## 🛠️ 技术栈

- **前端框架**: Streamlit
- **数据处理**: Pandas, NumPy
- **可视化**: Matplotlib, Seaborn, WordCloud
- **NLP**: Jieba 分词, DashScope Text Embedding API
- **机器学习**: Scikit-learn (KMeans), PyTorch (MLP 神经网络)
- **大模型**: 阿里云 DashScope (通义千问 qwen-turbo)
- **语言**: Python 3.11
