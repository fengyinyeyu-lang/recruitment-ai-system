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

    # 提取每个聚类的核心关键词（过滤非技能噪声词）
    order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
    terms = vectorizer.get_feature_names_out()
    cluster_keywords = {}
    for i in range(n_clusters):
        # 方案1改进：扩大候选词池至 100 个，经过滤后再取前 10 个有效词，防止核心技能词落榜
        top_words_candidates = [terms[ind] for ind in order_centroids[i, :100]]
        from src.data_pipeline.nlp_processor import filter_words
        
        # filter_words 会剔除 NOISE_WORDS 里的词，返回过滤后以逗号分隔的字符串
        filtered_words_str = filter_words(top_words_candidates)
        
        # 将逗号分隔的字符串拆分并去除空字符串（防御性编程：防止出现空项）
        valid_words = [w.strip() for w in filtered_words_str.split(',') if w.strip()]
        
        # 截取前 10 个高质量的有效技能词重新拼接展示
        cluster_keywords[i] = ", ".join(valid_words[:10])

    # PCA 降维用于可视化
    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(X.toarray())
    sample_df['pca_x'] = coords[:, 0]
    sample_df['pca_y'] = coords[:, 1]

    logging.info(f"聚类完成，共 {n_clusters} 个簇。")
    return sample_df, cluster_keywords
