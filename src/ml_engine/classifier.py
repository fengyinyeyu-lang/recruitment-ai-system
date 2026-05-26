"""
分类器模块（模块4扩展）
基于大模型 Embedding + PyTorch 全连接神经网络 (MLP) 的岗位智能分类。

指导书 5.4 节要求：使用神经网络分类算法，结合大模型 Embedding 文本表示进行
机器学习与自动识别。标签来源为 KMeans 聚类生成的伪标签。
"""
import os
import logging
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 项目根目录 & 默认模型保存路径
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DEFAULT_MODEL_PATH = os.path.join(PROJECT_ROOT, 'models', 'nn_classifier.pt')


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
