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
    import re
    stopwords = {'的', '了', '在', '是', '有', '和', '不', '人', '都', '要',
                 '也', '就', '到', '说', '会', '你', '我', '他', '她', '这',
                 'br', '熟悉', '使用', '能力', '相关', '以上', '工作', '经验',
                 '优先', '负责', '进行', '具备', '良好', '能够', '项目', '开发',
                 '技术', '公司', '团队', '参与', '了解', '系统', '岗位', '职位'}

    def clean_and_cut(text):
        if pd.isna(text):
            return ""
        text = re.sub(r'<[^>]+>', ' ', str(text))
        words = jieba.cut(text)
        return " ".join([w for w in words if len(w) > 1 and w not in stopwords])

    return df[text_col].apply(clean_and_cut)


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

    logging.info(f"开始聚类分析，采样 {len(sample_df)} 条数据...")

    # 文本预处理
    processed_texts = preprocess_texts(sample_df)

    # TF-IDF 向量化
    vectorizer = TfidfVectorizer(max_features=max_features)
    X = vectorizer.fit_transform(processed_texts)

    # KMeans 训练
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    sample_df['cluster'] = kmeans.fit_predict(X)

    # 提取每个聚类的核心关键词
    order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
    terms = vectorizer.get_feature_names_out()
    cluster_keywords = {}
    for i in range(n_clusters):
        top_words = [terms[ind] for ind in order_centroids[i, :8]]
        cluster_keywords[i] = ", ".join(top_words)

    # PCA 降维用于可视化
    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(X.toarray())
    sample_df['pca_x'] = coords[:, 0]
    sample_df['pca_y'] = coords[:, 1]

    logging.info(f"聚类完成，共 {n_clusters} 个簇。")
    return sample_df, cluster_keywords
