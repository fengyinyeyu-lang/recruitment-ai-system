"""
分类器模块（模块4扩展）
基于朴素贝叶斯的岗位智能分类预测。
"""
import pandas as pd
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report


def train_classification_model(df, text_col='positionDetail', label_col='keyword', sample_size=10000):
    """
    训练朴素贝叶斯文本分类器

    参数:
        df: 清洗后的 DataFrame
        text_col: 文本特征列
        label_col: 标签列（岗位关键字）
        sample_size: 采样量

    返回:
        (准确率, 模型, 向量器, 分类报告字符串)
    """
    # 过滤掉样本数过少的稀有类别，可以显著提升分类器准确率
    counts = df[label_col].value_counts()
    valid_labels = counts[counts >= 50].index
    filtered_df = df[df[label_col].isin(valid_labels)]

    # 采样
    if len(filtered_df) > sample_size:
        sample_df = filtered_df.sample(sample_size, random_state=42).copy()
    else:
        sample_df = filtered_df.copy()

    # 分词
    texts = sample_df[text_col].fillna('').apply(
        lambda x: " ".join(jieba.cut(str(x)))
    )
    labels = sample_df[label_col]

    # TF-IDF 向量化
    vectorizer = TfidfVectorizer(max_features=1500, min_df=3)
    X = vectorizer.fit_transform(texts)
    y = labels

    # 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # 训练朴素贝叶斯
    model = MultinomialNB()
    model.fit(X_train, y_train)

    # 评估
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, zero_division=0)

    return acc, model, vectorizer, report


def predict_job_category(text, model, vectorizer):
    """
    对单条岗位描述进行分类预测
    """
    processed = " ".join(jieba.cut(str(text)))
    vec = vectorizer.transform([processed])
    pred = model.predict(vec)[0]
    return pred
