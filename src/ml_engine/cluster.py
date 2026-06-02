"""
机器学习聚类模块（模块4）
使用 KMeans 对招聘岗位描述进行无监督聚类分析。
"""
import pandas as pd
import numpy as np
import jieba
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def preprocess_texts(df, text_col='positionDetail'):
    """
    对岗位描述列进行文本预处理（清洗+分词）
    返回分词后的文本 Series
    """
    from src.data_pipeline.nlp_processor import preprocess_text_column
    return preprocess_text_column(df, text_col)


import streamlit as st

@st.cache_data(show_spinner=False)
def perform_kmeans_clustering(df, n_clusters=5, max_features=1000, sample_size=3000):
    """
    执行 KMeans 聚类分析

    参数:
        df: 清洗后的 DataFrame
        n_clusters: 聚类数
        max_features: TF-IDF 最大特征数
        sample_size: 采样数（加速训练）

    返回:
        (带聚类标签的 DataFrame, 每个聚类的核心关键词字典, PCA降维坐标 DataFrame)
    """
    # 采样以加速
    if len(df) > sample_size:
        sample_df = df.sample(sample_size, random_state=42).copy()
    else:
        sample_df = df.copy()

    logging.info(f"开始聚类分析，采样 {len(sample_df)} 条数据 (已应用最新停用词)...")

    # 文本预处理
    processed_texts = preprocess_texts(sample_df)

    # TF-IDF 向量化
    vectorizer = TfidfVectorizer(max_features=max_features)
    X = vectorizer.fit_transform(processed_texts)

    # KMeans 训练
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    sample_df['cluster'] = kmeans.fit_predict(X)

    # 提取每个聚类的核心关键词（白名单准入 + 英文黑名单拦截）
    order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
    terms = vectorizer.get_feature_names_out()
    cluster_keywords = {}
    
    # 高纯度 IT 中文技术白名单（只有这些中文词才有资格出现在特征词画像中）
    IT_TECH_CN = {
        '前端', '后端', '测试', '运维', '算法', '架构', '数据', '模型',
        '嵌入式', '爬虫', '视觉', '微服务', '分布式', '全栈', '硬件',
        '客户端', '游戏', '人工智能', '深度学习', '机器学习', '图像',
        '大数据', '云计算', '网络安全', '中间件', '渲染', '微调',
        '安全', '音频', '识别', '挖掘', '接口', '框架', '引擎',
        '仿真', '固件', '驱动', '协议', '编译', '容器', '虚拟化',
        '自动化', '智能', '语音', '搜索', '推荐', '风控', '量化',
    }
    
    # 英文黑名单：招聘 JD 中常见的纯英文非技术词（国名、职位、业务泛词等）
    ENG_BLACKLIST = {
        # 国家/地名
        'china', 'beijing', 'shanghai', 'shenzhen', 'hangzhou', 'guangzhou',
        'nanjing', 'chengdu', 'wuhan', 'xian', 'suzhou', 'tianjin',
        # 职位/角色/头衔
        'manager', 'leader', 'director', 'senior', 'junior', 'intern',
        'engineer', 'developer', 'designer', 'architect', 'specialist',
        'officer', 'executive', 'supervisor', 'coordinator', 'consultant',
        'analyst', 'associate', 'assistant', 'head', 'lead', 'chief',
        'vp', 'cto', 'ceo', 'coo', 'cfo', 'cso', 'staff', 'principal',
        # 业务/管理泛词
        'team', 'project', 'product', 'business', 'service', 'support',
        'market', 'sales', 'customer', 'client', 'partner', 'company',
        'group', 'global', 'local', 'remote', 'onsite', 'hybrid',
        'design', 'plan', 'strategy', 'process', 'solution', 'system',
        'experience', 'skill', 'ability', 'knowledge', 'degree',
        'year', 'years', 'month', 'day', 'time', 'work', 'job',
        'good', 'strong', 'great', 'best', 'new', 'high', 'low',
        'base', 'based', 'related', 'required', 'preferred',
        'and', 'the', 'for', 'with', 'from', 'this', 'that',
        'will', 'can', 'may', 'must', 'should', 'need',
        'etc', 'e.g', 'i.e', 'ok', 'yes', 'no',
        # 招聘中常见的英文缩写噪声
        'gs', 'cdp', 'tdi', 'tse', 'ba', 'pm', 'hr', 'hc',
        'jd', 'kpi', 'okr', 'roi', 'prd', 'brd', 'sop',
        'feed', 'pass', 'open', 'free', 'pro', 'plus', 'max', 'top',
        'hrbp', 'aps', 'mj', 'tdl', 'emc', 'ei',
    }
    
    import re
    
    for i in range(n_clusters):
        # 扩大候选词池至 300 个，确保能在沙里淘出真金
        candidate_count = min(300, len(terms))
        top_words_candidates = [terms[ind] for ind in order_centroids[i, :candidate_count]]
        
        valid_words = []
        for w in top_words_candidates:
            w = w.strip().lower()
            if not w:
                continue
            # 单字符特殊放行（仅限已知的单字母技术名称）
            if len(w) < 2 and w not in ('c', 'r'):
                continue
                
            # 特征判断1：纯英文/数字/技术符号组成
            is_eng_tech = bool(re.match(r'^[a-z0-9\+#\.]+$', w))
            
            if is_eng_tech:
                # 英文词必须不在黑名单中才放行
                if w in ENG_BLACKLIST:
                    continue
                if w not in valid_words:
                    valid_words.append(w)
            elif w in IT_TECH_CN:
                # 中文词必须在白名单中
                if w not in valid_words:
                    valid_words.append(w)
            
            # 取满10个即可
            if len(valid_words) >= 10:
                break
        
        cluster_keywords[i] = ", ".join(valid_words) if valid_words else "无典型IT技术特征"

    # PCA 降维用于可视化
    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(X.toarray())
    sample_df['pca_x'] = coords[:, 0]
    sample_df['pca_y'] = coords[:, 1]

    logging.info(f"聚类完成，共 {n_clusters} 个簇。")
    return sample_df, cluster_keywords
