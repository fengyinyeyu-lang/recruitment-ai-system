"""
NLP 文本预处理模块
负责分词、去停用词、TF-IDF 特征提取等文本工程化操作。
"""
import jieba
import re
import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

# 项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# 默认停用词表（常见高频无意义词）
DEFAULT_STOPWORDS = {
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
    '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着',
    '没有', '看', '好', '自己', '这', '他', '她', '吗', '知道', '啊',
    '熟悉', '能够', '具有', '相关', '以上', '经验', '优先', '以及',
    '工作', '负责', '能力', '进行', '公司', '岗位', '职位', '描述',
    '要求', 'br', '具备', '良好', '技术', '使用', '开发', '项目',
}


def clean_html_tags(text):
    """移除 HTML 标签和多余空白"""
    if pd.isna(text):
        return ""
    text = re.sub(r'<[^>]+>', ' ', str(text))
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def tokenize(text, stopwords=None):
    """使用 jieba 分词并过滤停用词"""
    if stopwords is None:
        stopwords = DEFAULT_STOPWORDS
    words = jieba.cut(str(text))
    return " ".join([w for w in words if len(w) > 1 and w not in stopwords])


def build_tfidf_matrix(texts, max_features=1000):
    """
    构建 TF-IDF 特征矩阵
    返回: (稀疏矩阵, TfidfVectorizer 实例)
    """
    vectorizer = TfidfVectorizer(max_features=max_features)
    X = vectorizer.fit_transform(texts)
    return X, vectorizer


def preprocess_text_column(df, text_col='positionDetail'):
    """
    对 DataFrame 中指定的文本列进行完整预处理：
    清洗 HTML -> 分词 -> 返回处理后的 Series
    """
    cleaned = df[text_col].apply(clean_html_tags)
    tokenized = cleaned.apply(tokenize)
    return tokenized
