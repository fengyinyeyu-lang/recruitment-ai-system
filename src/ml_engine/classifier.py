"""
分类器模块（模块4扩展）
基于大模型 Embedding + PyTorch 全连接神经网络 (MLP) 的岗位智能分类。

指导书 5.4 节要求：使用神经网络分类算法，结合大模型 Embedding 文本表示进行
机器学习与自动识别。标签来源为 KMeans 聚类生成的伪标签。
"""
import os
import re
import logging
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, mean_absolute_error, r2_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import pandas as pd
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 项目根目录 & 默认模型保存路径
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DEFAULT_MODEL_PATH = os.path.join(PROJECT_ROOT, 'models', 'nn_classifier.pt')
SALARY_MODEL_PATH = os.path.join(PROJECT_ROOT, 'models', 'salary_predictor.pkl')
SALARY_ENCODERS_PATH = os.path.join(PROJECT_ROOT, 'models', 'salary_encoders.json')


class JobClassifierNN(nn.Module):
    """
    岗位分类全连接神经网络 (MLP)

    结构：
        Linear(embedding_dim, 256) → ReLU → Dropout(0.3)
        → Linear(256, 64) → ReLU
        → Linear(64, num_classes)
    """

    def __init__(self, input_dim, num_classes):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Linear(64, num_classes),
        )

    def forward(self, x):
        return self.network(x)


def train(X, y, save_path=None, epochs=30, batch_size=64,
          learning_rate=1e-3, progress_callback=None):
    """
    训练 MLP 神经网络分类器。

    参数:
        X: np.ndarray, 形状 (n_samples, embedding_dim)，Embedding 特征矩阵
        y: np.ndarray, 形状 (n_samples,)，整数标签（如 KMeans 聚类伪标签）
        save_path: 模型保存路径，默认 models/nn_classifier.pt
        epochs: 训练轮次
        batch_size: 批大小
        learning_rate: 学习率
        progress_callback: 可选回调 callback(epoch, epochs, train_loss, val_acc)

    返回:
        (测试集准确率, 训练历史 dict, 分类报告字符串)
    """
    if save_path is None:
        save_path = DEFAULT_MODEL_PATH

    num_classes = len(np.unique(y))
    input_dim = X.shape[1]
    logging.info("训练参数 — 样本: %d, 维度: %d, 类别: %d", len(X), input_dim, num_classes)

    # 划分训练集 / 测试集
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logging.info("使用设备: %s", device)

    X_train_t = torch.FloatTensor(X_train).to(device)
    X_test_t = torch.FloatTensor(X_test).to(device)
    y_train_t = torch.LongTensor(y_train).to(device)
    y_test_t = torch.LongTensor(y_test).to(device)

    train_loader = DataLoader(
        TensorDataset(X_train_t, y_train_t),
        batch_size=batch_size, shuffle=True
    )

    # 初始化模型
    model = JobClassifierNN(input_dim, num_classes).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='max', patience=5, factor=0.5
    )

    # 训练循环
    history = {'train_loss': [], 'val_acc': []}
    best_acc = 0.0

    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        n_batches = 0

        for bx, by in train_loader:
            optimizer.zero_grad()
            loss = criterion(model(bx), by)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            n_batches += 1

        avg_loss = total_loss / max(n_batches, 1)

        # 验证
        model.eval()
        with torch.no_grad():
            val_preds = torch.argmax(model(X_test_t), dim=1).cpu().numpy()
            val_acc = accuracy_score(y_test, val_preds)

        history['train_loss'].append(avg_loss)
        history['val_acc'].append(val_acc)
        scheduler.step(val_acc)

        # 保存最佳模型
        if val_acc > best_acc:
            best_acc = val_acc
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            torch.save({
                'model_state_dict': model.state_dict(),
                'input_dim': input_dim,
                'num_classes': num_classes,
            }, save_path)

        if progress_callback:
            progress_callback(epoch + 1, epochs, avg_loss, val_acc)

        if (epoch + 1) % 5 == 0 or epoch == 0:
            logging.info(
                "Epoch [%d/%d] Loss: %.4f  Val Acc: %.4f  (Best: %.4f)",
                epoch + 1, epochs, avg_loss, val_acc, best_acc
            )

    # 用最佳模型做最终评估
    ckpt = torch.load(save_path, map_location=device, weights_only=False)
    model.load_state_dict(ckpt['model_state_dict'])
    model.eval()

    with torch.no_grad():
        final_preds = torch.argmax(model(X_test_t), dim=1).cpu().numpy()

    final_acc = accuracy_score(y_test, final_preds)
    report = classification_report(y_test, final_preds, zero_division=0)
    logging.info("最终测试集准确率: %.4f", final_acc)
    logging.info("模型已保存至: %s", save_path)

    return final_acc, history, report


def predict(X, model_path=None):
    """
    使用已保存的 MLP 模型对 Embedding 矩阵进行分类预测。

    参数:
        X: np.ndarray, 形状 (n_samples, embedding_dim)
        model_path: 模型文件路径，默认 models/nn_classifier.pt

    返回:
        labels: np.ndarray, 形状 (n_samples,)，预测的整数标签
    """
    if model_path is None:
        model_path = DEFAULT_MODEL_PATH

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"模型文件不存在: {model_path}，请先训练模型。")

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    ckpt = torch.load(model_path, map_location=device, weights_only=False)

    model = JobClassifierNN(ckpt['input_dim'], ckpt['num_classes']).to(device)
    model.load_state_dict(ckpt['model_state_dict'])
    model.eval()

    X_t = torch.FloatTensor(np.asarray(X)).to(device)
    with torch.no_grad():
        labels = torch.argmax(model(X_t), dim=1).cpu().numpy()

    return labels


# =====================================================================
# 薪资预测模块 — 基于 RandomForest 的回归模型
# 使用城市、学历、工作经验、岗位类别等特征预测平均薪资
# =====================================================================

def _encode_salary_features(df):
    """
    对薪资预测所需的特征进行编码和预处理。
    返回 (特征矩阵, 目标值, 编码器字典)
    """
    data = df.copy()

    # 只保留有薪资数据的行
    data = data.dropna(subset=['salary_avg'])

    # 特征工程
    features = pd.DataFrame(index=data.index)

    # 城市编码
    if 'city' in data.columns:
        features['city'] = data['city'].fillna('未知')

    # 学历编码
    if 'education' in data.columns:
        features['education'] = data['education'].fillna('不限')

    # 工作年限数值化
    # 工作年限数值化
    work_year_col = 'workYear' if 'workYear' in data.columns else ('work_year' if 'work_year' in data.columns else None)
    if work_year_col:
        def parse_exp(x):
            if pd.isna(x):
                return 0
            x = str(x)
            if '不限' in x:
                return 0
            if '应届' in x:
                return 0
            nums = re.findall(r'\d+', x)
            if nums:
                return int(nums[-1])
            return 0
        features['exp_years'] = data[work_year_col].apply(parse_exp)

    # 岗位类别编码
    if 'keyword' in data.columns:
        features['keyword'] = data['keyword'].fillna('其他')

    # 公司规模编码
    # 公司规模编码
    company_size_col = 'companySize' if 'companySize' in data.columns else ('company_size' if 'company_size' in data.columns else None)
    if company_size_col:
        features['company_size'] = data[company_size_col].fillna('未知')

    # 行业领域编码
    industry_col = 'industryField' if 'industryField' in data.columns else ('industry_field' if 'industry_field' in data.columns else None)
    if industry_col:
        features['industry'] = data[industry_col].fillna('未知')
        features['industry'] = features['industry'].str.split(',').str[0].str.strip()

    # 目标值
    y = data['salary_avg'].values

    # 对类别特征进行 Label Encoding
    encoders = {}
    cat_cols = features.select_dtypes(include=['object']).columns
    for col in cat_cols:
        le = LabelEncoder()
        features[col] = features[col].astype(str)
        features[col] = le.fit_transform(features[col])
        encoders[col] = {label: int(code) for label, code in zip(le.classes_, le.transform(le.classes_))}

    return features.values, y, encoders, features.columns.tolist()


def train_salary_predictor(df):
    """
    训练薪资预测模型（RandomForest回归）。

    参数:
        df: 清洗后的DataFrame

    返回:
        (model, metrics_dict) 训练好的模型和评估指标
    """
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error, r2_score
    import re

    X, y, encoders, feature_names = _encode_salary_features(df)

    if len(X) < 100:
        raise ValueError(f"数据量不足（{len(X)}条），无法训练可靠的薪资预测模型")

    # 划分训练集/测试集
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # 训练 RandomForest 回归模型
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=15,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    # 评估
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    metrics = {
        'mae': float(mae),
        'r2': float(r2),
        'samples': len(X),
        'feature_names': feature_names,
        'feature_importance': {
            name: float(imp)
            for name, imp in zip(feature_names, model.feature_importances_)
        }
    }

    # 保存模型和编码器
    os.makedirs(os.path.dirname(SALARY_MODEL_PATH), exist_ok=True)
    import pickle
    with open(SALARY_MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    with open(SALARY_ENCODERS_PATH, 'w', encoding='utf-8') as f:
        json.dump({'encoders': encoders, 'feature_names': feature_names}, f, ensure_ascii=False)

    logging.info(f"薪资预测模型训练完成: MAE={mae:.2f}, R²={r2:.4f}")

    return model, metrics


def predict_salary(features_dict, model=None):
    """
    使用训练好的模型预测薪资。

    参数:
        features_dict: dict，包含 city, education, workYear, keyword 等特征
        model: 可选，已加载的模型

    返回:
        predicted_salary: float，预测的平均薪资（K）
        confidence: str，置信度描述
    """
    import pickle
    import re

    # 加载模型和编码器
    if model is None:
        if not os.path.exists(SALARY_MODEL_PATH):
            raise FileNotFoundError("薪资预测模型不存在，请先训练模型。")
        with open(SALARY_MODEL_PATH, 'rb') as f:
            model = pickle.load(f)

    if not os.path.exists(SALARY_ENCODERS_PATH):
        raise FileNotFoundError("编码器文件不存在，请先训练模型。")

    with open(SALARY_ENCODERS_PATH, 'r', encoding='utf-8') as f:
        enc_data = json.load(f)
    encoders = enc_data['encoders']
    feature_names = enc_data['feature_names']

    # 构建特征向量
    feature_vec = []
    
    edu_map = {
        "大专": "大学专科",
        "本科": "大学本科",
        "硕士": "硕士研究生",
        "博士": "博士研究生",
        "高中": "普通高中",
        "中专": "中等专科"
    }

    for col in feature_names:
        if col in encoders:
            # 类别特征
            val = features_dict.get(col, '未知')
            val_str = str(val).strip()
            
            # 对关键字转大写
            if col == 'keyword':
                val_str = val_str.upper()
                
            if val_str in encoders[col]:
                feature_vec.append(encoders[col][val_str])
            else:
                # 尝试别名映射
                matched = False
                if col == 'city':
                    city_with_shi = val_str + "市"
                    if city_with_shi in encoders[col]:
                        feature_vec.append(encoders[col][city_with_shi])
                        matched = True
                elif col == 'education':
                    mapped_edu = edu_map.get(val_str, val_str)
                    if mapped_edu in encoders[col]:
                        feature_vec.append(encoders[col][mapped_edu])
                        matched = True
                
                if not matched:
                    feature_vec.append(0)
        elif col == 'exp_years':
            # 数值特征
            val = features_dict.get('workYear', '0')
            if isinstance(val, (int, float)):
                feature_vec.append(val)
            else:
                nums = re.findall(r'\d+', str(val))
                feature_vec.append(int(nums[-1]) if nums else 0)
        else:
            feature_vec.append(0)

    X = np.array([feature_vec])
    pred = model.predict(X)[0]

    # 置信度评估
    if hasattr(model, 'estimators_'):
        # 用树的方差评估置信度
        all_preds = np.array([tree.predict(X)[0] for tree in model.estimators_])
        std = np.std(all_preds)
        if std < 2:
            confidence = "高"
        elif std < 5:
            confidence = "中"
        else:
            confidence = "较低"
    else:
        confidence = "中"

    return round(float(pred), 1), confidence
