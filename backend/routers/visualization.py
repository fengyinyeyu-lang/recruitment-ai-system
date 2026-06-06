"""可视化数据路由 - 返回 ECharts 可渲染的 JSON 数据"""
from typing import Optional
import numpy as np
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from backend.dependencies import get_data_df, get_count_df, get_current_user
from backend.schemas.models import ApiResponse

router = APIRouter(prefix="/api/visualization", tags=["可视化"])


@router.get("/salary", response_model=ApiResponse)
def get_salary_distribution(username: str = Depends(get_current_user)):
    """返回薪资分布数据（直方图 bins+counts、KDE 曲线、统计量）"""
    df = get_data_df()
    if df is None or df.empty or 'salary_avg' not in df.columns:
        return ApiResponse(data=None, message="暂无薪资数据")

    data = df['salary_avg'].dropna().values
    if len(data) == 0:
        return ApiResponse(data=None, message="暂无薪资数据")

    # 直方图
    counts, bin_edges = np.histogram(data, bins=25)
    bins = [round((bin_edges[i] + bin_edges[i + 1]) / 2, 1) for i in range(len(counts))]
    counts = counts.tolist()

    # KDE 曲线（使用 scipy）
    try:
        from scipy.stats import gaussian_kde
        kde = gaussian_kde(data)
        kde_x = np.linspace(data.min(), data.max(), 200).tolist()
        kde_y = kde(kde_x).tolist()
    except Exception:
        kde_x = []
        kde_y = []

    # 统计量
    mean_val = round(float(np.mean(data)), 1)
    median_val = round(float(np.median(data)), 1)
    p25 = round(float(np.percentile(data, 25)), 1)
    p75 = round(float(np.percentile(data, 75)), 1)

    return ApiResponse(data={
        "bins": bins,
        "counts": counts,
        "kde_x": kde_x,
        "kde_y": kde_y,
        "mean": mean_val,
        "median": median_val,
        "p25": p25,
        "p75": p75,
    })


@router.get("/city-salary", response_model=ApiResponse)
def get_city_salary(username: str = Depends(get_current_user)):
    """返回 Top15 城市薪资数据"""
    df = get_data_df()
    if df is None or df.empty or 'city' not in df.columns or 'salary_avg' not in df.columns:
        return ApiResponse(data=None, message="暂无城市薪资数据")

    city_salary = df.groupby('city')['salary_avg'].agg(['mean', 'count']).sort_values('mean', ascending=False).head(15)

    return ApiResponse(data={
        "cities": city_salary.index.tolist(),
        "salaries": [round(v, 1) for v in city_salary['mean'].tolist()],
        "counts": city_salary['count'].tolist(),
    })


@router.get("/education", response_model=ApiResponse)
def get_education_distribution(username: str = Depends(get_current_user)):
    """返回学历分布数据"""
    df = get_data_df()
    if df is None or df.empty or 'education' not in df.columns:
        return ApiResponse(data=None, message="暂无学历数据")

    edu_counts = df['education'].value_counts()
    total = edu_counts.sum()

    return ApiResponse(data={
        "labels": edu_counts.index.tolist(),
        "values": edu_counts.values.tolist(),
        "percentages": [round(v / total * 100, 1) for v in edu_counts.values],
    })


@router.get("/experience-salary", response_model=ApiResponse)
def get_experience_salary(username: str = Depends(get_current_user)):
    """返回经验薪资箱线图数据"""
    df = get_data_df()
    if df is None or df.empty:
        return ApiResponse(data=None, message="暂无数据")

    exp_col = 'workYear' if 'workYear' in df.columns else 'work_year'
    if exp_col not in df.columns or 'salary_avg' not in df.columns:
        return ApiResponse(data=None, message="暂无经验薪资数据")

    order = ['应届生', '1年以下', '1-3年', '3-5年', '5-10年', '10年以上', '经验不限']
    existing_order = [o for o in order if o in df[exp_col].unique()]
    if not existing_order:
        existing_order = df[exp_col].value_counts().index.tolist()

    categories = []
    data = []
    for cat in existing_order:
        cat_data = df[df[exp_col] == cat]['salary_avg'].dropna().values
        if len(cat_data) == 0:
            continue
        categories.append(cat)
        data.append({
            "min": round(float(np.min(cat_data)), 1),
            "q1": round(float(np.percentile(cat_data, 25)), 1),
            "median": round(float(np.median(cat_data)), 1),
            "q3": round(float(np.percentile(cat_data, 75)), 1),
            "max": round(float(np.max(cat_data)), 1),
            "mean": round(float(np.mean(cat_data)), 1),
        })

    return ApiResponse(data={
        "categories": categories,
        "data": data,
    })


@router.get("/position-demand", response_model=ApiResponse)
def get_position_demand(username: str = Depends(get_current_user)):
    """返回岗位需求数据"""
    count_df = get_count_df()
    if count_df is None or count_df.empty:
        # 从主数据中统计
        df = get_data_df()
        if df is None or df.empty or 'keyword' not in df.columns:
            return ApiResponse(data=None, message="暂无岗位需求数据")
        kw_counts = df['keyword'].value_counts().head(15)
        return ApiResponse(data={
            "keywords": kw_counts.index.tolist(),
            "counts": kw_counts.values.tolist(),
        })

    top = count_df.head(15)
    return ApiResponse(data={
        "keywords": top['keyword'].tolist(),
        "counts": top['count'].tolist(),
    })


class WordCloudRequest(BaseModel):
    sample_size: int = 2000


@router.post("/wordcloud", response_model=ApiResponse)
def get_wordcloud(req: WordCloudRequest, username: str = Depends(get_current_user)):
    """返回词频数据 [{text, weight}]，前端用 echarts-wordcloud 渲染"""
    import jieba
    from src.data_pipeline.nlp_processor import DEFAULT_STOPWORDS, NOISE_WORDS, clean_text

    df = get_data_df()
    if df is None or df.empty:
        return ApiResponse(data={"words": []})

    # 采样
    sample_size = min(req.sample_size, len(df))
    sample_df = df.sample(sample_size, random_state=42)

    # 合并文本
    text_data = []
    for col in ['positionDetail', 'positionName', 'keyword']:
        if col in sample_df.columns:
            text_data += sample_df[col].dropna().astype(str).tolist()
    if not text_data:
        return ApiResponse(data={"words": []})

    raw_text = ' '.join(text_data)
    raw_text = clean_text(raw_text)

    # 分词
    all_stopwords = DEFAULT_STOPWORDS | NOISE_WORDS
    words = [w for w in jieba.cut(raw_text) if len(w) > 1 and w not in all_stopwords]

    # 统计词频
    from collections import Counter
    word_counts = Counter(words).most_common(150)

    words_list = [{"text": w, "weight": c} for w, c in word_counts]
    return ApiResponse(data={"words": words_list})


@router.get("/city-demand", response_model=ApiResponse)
def get_city_demand(username: str = Depends(get_current_user)):
    """返回城市需求 Top15"""
    df = get_data_df()
    if df is None or df.empty or 'city' not in df.columns:
        return ApiResponse(data=None, message="暂无城市需求数据")

    city_counts = df['city'].value_counts().head(15)
    return ApiResponse(data={
        "cities": city_counts.index.tolist(),
        "counts": city_counts.values.tolist(),
    })


@router.get("/industry", response_model=ApiResponse)
def get_industry_distribution(username: str = Depends(get_current_user)):
    """返回行业分布 Top15"""
    df = get_data_df()
    if df is None or df.empty:
        return ApiResponse(data=None, message="暂无行业数据")

    ind_col = 'industryField' if 'industryField' in df.columns else 'industry_field'
    if ind_col not in df.columns:
        return ApiResponse(data=None, message="暂无行业数据")

    industries = df[ind_col].dropna().str.split(',').explode().str.strip()
    industry_counts = industries.value_counts().head(15)

    return ApiResponse(data={
        "industries": industry_counts.index.tolist(),
        "counts": industry_counts.values.tolist(),
    })
