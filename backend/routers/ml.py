"""机器学习路由 - KMeans 聚类、神经网络训练/预测、薪资预测"""
import pandas as pd
import numpy as np
import uuid
import threading
from collections import Counter
from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_data_df, get_current_user
from backend.schemas.models import (
    KMeansRequest, KMeansResult, NNTrainRequest, NNTrainResult,
    NNPredictRequest, NNPredictResult, SalaryPredictRequest, SalaryPredictResult,
    ApiResponse,
)

router = APIRouter(prefix="/api/ml", tags=["机器学习"])

# 训练进度存储 {task_id: {progress, epoch, epochs, loss, acc, status, result}}
_training_progress = {}


@router.get("/nn-progress/{task_id}", response_model=ApiResponse)
def get_nn_progress(task_id: str, username: str = Depends(get_current_user)):
    """获取神经网络训练进度"""
    if task_id not in _training_progress:
        raise HTTPException(status_code=404, detail="任务不存在")
    return ApiResponse(data=_training_progress[task_id])


@router.post("/kmeans", response_model=ApiResponse)
def run_kmeans(req: KMeansRequest, username: str = Depends(get_current_user)):
    """执行 KMeans 聚类，返回关键词、PCA 数据、样本数据"""
    from src.ml_engine.cluster import perform_kmeans_clustering

    df = get_data_df()
    if df is None or df.empty:
        raise HTTPException(status_code=400, detail="暂无数据，无法执行聚类")

    try:
        clustered_df, keywords = perform_kmeans_clustering(df, n_clusters=req.n_clusters)

        # PCA 数据
        pca_data = []
        if 'pca_x' in clustered_df.columns and 'pca_y' in clustered_df.columns:
            for _, row in clustered_df.iterrows():
                pca_data.append({
                    "x": round(float(row['pca_x']), 3),
                    "y": round(float(row['pca_y']), 3),
                    "cluster": int(row['cluster']),
                })

        # 样本数据
        sample_data = []
        display_cols = ['positionName', 'city', 'salary', 'workYear', 'cluster']
        available_cols = [c for c in display_cols if c in clustered_df.columns]
        for _, row in clustered_df[available_cols].head(15).iterrows():
            item = {}
            for col in available_cols:
                val = row[col]
                if hasattr(val, 'item'):
                    val = val.item()
                item[col] = val
            sample_data.append(item)

        # 各簇统计信息（平均薪资、主要城市、主要岗位）
        cluster_stats = {}
        for _, row in clustered_df.iterrows():
            cid = int(row['cluster'])
            if cid not in cluster_stats:
                cluster_stats[cid] = {
                    'count': 0, 'salaries': [], 'cities': [], 'positions': [],
                }
            cs = cluster_stats[cid]
            cs['count'] += 1
            if 'salary_avg' in clustered_df.columns and not pd.isna(row.get('salary_avg')):
                cs['salaries'].append(row['salary_avg'])
            city_val = row.get('city', '')
            if city_val and not pd.isna(city_val):
                cs['cities'].append(str(city_val))
            pos_val = row.get('positionName', '') or row.get('position_name', '')
            if pos_val and not pd.isna(pos_val):
                cs['positions'].append(str(pos_val))

        stats_list = []
        for cid in sorted(cluster_stats.keys()):
            cs = cluster_stats[cid]
            avg_sal = round(float(np.mean(cs['salaries'])), 1) if cs['salaries'] else 0.0
            # 主要城市 Top 3
            top_cities = [city for city, _ in Counter(cs['cities']).most_common(3)]
            top_positions = [pos for pos, _ in Counter(cs['positions']).most_common(3)]
            stats_list.append({
                'cluster': cid + 1,
                'count': cs['count'],
                'avg_salary': avg_sal,
                'top_city': '、'.join(top_cities),
                'top_position': '、'.join(top_positions),
            })

        return ApiResponse(data={
            "keywords": keywords,
            "pca_data": pca_data,
            "sample_data": sample_data,
            "cluster_stats": stats_list,
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"聚类分析失败: {str(e)}")


@router.post("/nn-train", response_model=ApiResponse)
def train_nn(req: NNTrainRequest, username: str = Depends(get_current_user)):
    """启动神经网络训练，返回 task_id 用于轮询进度"""
    task_id = str(uuid.uuid4())[:8]
    _training_progress[task_id] = {
        "progress": 0, "epoch": 0, "epochs": req.epochs,
        "loss": 0, "acc": 0, "status": "preparing", "result": None
    }

    def _train_task():
        try:
            from src.data_pipeline.nlp_processor import build_embedding_matrix
            from src.ml_engine import classifier
            from sklearn.cluster import KMeans
            from sklearn.feature_extraction.text import TfidfVectorizer
            from src.data_pipeline.nlp_processor import DEFAULT_STOPWORDS, clean_text, tokenize, get_sampled_df, filter_words

            df = get_data_df()
            if df is None or df.empty:
                _training_progress[task_id]["status"] = "failed"
                _training_progress[task_id]["result"] = {"error": "暂无数据"}
                return

            # Step 1: 获取 Embedding
            _training_progress[task_id]["status"] = "embedding"
            _training_progress[task_id]["progress"] = 5
            X = build_embedding_matrix(df, text_col='positionDetail', cache_name='classifier_emb_v3')

            # Step 2: KMeans 生成伪标签
            _training_progress[task_id]["status"] = "clustering"
            _training_progress[task_id]["progress"] = 15
            kmeans = KMeans(n_clusters=req.k, random_state=42, n_init=10)
            y = kmeans.fit_predict(X)

            # 动态提取各簇特征词
            cluster_names = {}
            sampled_df = get_sampled_df(df, len(y))

            if 'positionDetail' in sampled_df.columns:
                raw_texts = sampled_df['positionDetail'].fillna('').astype(str).tolist()
            else:
                parts = []
                if 'positionName' in sampled_df.columns:
                    parts.append(sampled_df['positionName'].fillna('').astype(str))
                if 'keyword' in sampled_df.columns:
                    parts.append(sampled_df['keyword'].fillna('').astype(str))
                if parts:
                    combined = parts[0]
                    for p in parts[1:]:
                        combined = combined + ' ' + p
                    raw_texts = combined.tolist()
                else:
                    raw_texts = [''] * len(sampled_df)

            sample_texts = [tokenize(clean_text(t)) for t in raw_texts]
            vec = TfidfVectorizer(min_df=5, stop_words=list(DEFAULT_STOPWORDS))
            tfidf_matrix = vec.fit_transform(sample_texts)
            feature_names = vec.get_feature_names_out()

            for c_idx in range(req.k):
                c_indices = [i for i, label in enumerate(y) if label == c_idx]
                other_indices = [i for i, label in enumerate(y) if label != c_idx]
                if c_indices and other_indices:
                    c_mean = np.asarray(tfidf_matrix[c_indices].mean(axis=0)).flatten()
                    other_mean = np.asarray(tfidf_matrix[other_indices].mean(axis=0)).flatten()
                    eps = 0.01
                    rel_spec = c_mean * np.log((c_mean + eps) / (other_mean + eps))
                    top_indices = rel_spec.argsort()[-5:][::-1]
                    top_words = filter_words([feature_names[i] for i in top_indices])
                    cluster_names[c_idx] = top_words
                elif c_indices:
                    c_mean = np.asarray(tfidf_matrix[c_indices].mean(axis=0)).flatten()
                    top_indices = c_mean.argsort()[-5:][::-1]
                    top_words = filter_words([feature_names[i] for i in top_indices])
                    cluster_names[c_idx] = top_words
                else:
                    cluster_names[c_idx] = "未知特征"

            # Step 3: 训练 MLP（带进度回调）
            _training_progress[task_id]["status"] = "training"

            def on_progress(epoch, epochs, loss, acc):
                pct = int(20 + (epoch / epochs) * 80)  # 20%~100%
                _training_progress[task_id].update({
                    "progress": pct,
                    "epoch": epoch,
                    "epochs": epochs,
                    "loss": round(float(loss), 4),
                    "acc": round(float(acc), 4),
                })

            acc, history, report = classifier.train(
                X, y, epochs=req.epochs, learning_rate=req.learning_rate,
                progress_callback=on_progress
            )

            serializable_history = {
                "train_loss": [round(float(v), 4) for v in history.get('train_loss', [])],
                "val_acc": [round(float(v), 4) for v in history.get('val_acc', [])],
            }

            _training_progress[task_id].update({
                "progress": 100,
                "status": "completed",
                "result": {
                    "accuracy": round(float(acc), 4),
                    "history": serializable_history,
                    "report": report,
                    "cluster_names": cluster_names,
                }
            })

        except Exception as e:
            _training_progress[task_id].update({
                "status": "failed",
                "result": {"error": str(e)}
            })

    # 在后台线程中启动训练
    thread = threading.Thread(target=_train_task, daemon=True)
    thread.start()

    return ApiResponse(data={"task_id": task_id})


@router.post("/nn-predict", response_model=ApiResponse)
def nn_predict(req: NNPredictRequest, username: str = Depends(get_current_user)):
    """使用神经网络预测"""
    from src.data_pipeline.nlp_processor import _call_embedding_api, clean_text
    from src.ml_engine import classifier

    try:
        cleaned = clean_text(req.description)
        if len(cleaned) > 2000:
            cleaned = cleaned[:2000]
        emb = _call_embedding_api([cleaned])
        pred_labels = classifier.predict(emb)
        p_label = int(pred_labels[0])

        return ApiResponse(data=NNPredictResult(
            cluster=p_label,
            cluster_name="",
        ).model_dump())

    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预测失败: {str(e)}")


@router.post("/salary-predict", response_model=ApiResponse)
def salary_predict(req: SalaryPredictRequest, username: str = Depends(get_current_user)):
    """薪资预测"""
    from src.ml_engine.classifier import predict_salary

    try:
        predicted, confidence = predict_salary({
            "city": req.city,
            "education": req.education,
            "workYear": req.workYear,
            "keyword": req.keyword,
        })

        return ApiResponse(data=SalaryPredictResult(
            predicted_salary=predicted,
            confidence=confidence,
        ).model_dump())

    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"薪资预测失败: {str(e)}")
