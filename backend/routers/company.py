"""企业画像路由 - 企业列表、企业详情画像"""
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.dependencies import get_data_df, get_current_user
from backend.schemas.models import CompanyProfile, ApiResponse

router = APIRouter(prefix="/api/company", tags=["企业画像"])


@router.get("/list", response_model=ApiResponse)
def get_company_list(username: str = Depends(get_current_user)):
    """返回 Top50 企业列表"""
    df = get_data_df()
    if df is None or df.empty:
        return ApiResponse(data=[])

    company_col = 'companyFullName' if 'companyFullName' in df.columns else 'company_full_name'
    short_col = 'companyShortName' if 'companyShortName' in df.columns else 'company_short_name'

    if company_col not in df.columns:
        return ApiResponse(data=[])

    company_counts = df[company_col].value_counts().head(50)
    results = []
    for company_name, count in company_counts.items():
        company_df = df[df[company_col] == company_name]
        short_name = company_df[short_col].iloc[0] if short_col in company_df.columns and len(company_df) > 0 else company_name
        avg_salary = round(float(company_df['salary_avg'].mean()), 1) if 'salary_avg' in company_df.columns else 0

        results.append({
            "name": company_name,
            "short_name": short_name,
            "job_count": int(count),
            "avg_salary": avg_salary,
        })

    return ApiResponse(data=results)


@router.get("/profile", response_model=ApiResponse)
def get_company_profile(name: str = Query(..., description="企业全称"), username: str = Depends(get_current_user)):
    """返回指定企业的完整画像数据"""
    import numpy as np

    df = get_data_df()
    if df is None or df.empty:
        raise HTTPException(status_code=400, detail="暂无数据")

    company_col = 'companyFullName' if 'companyFullName' in df.columns else 'company_full_name'
    short_col = 'companyShortName' if 'companyShortName' in df.columns else 'company_short_name'

    if company_col not in df.columns:
        raise HTTPException(status_code=400, detail="数据中缺少企业名称字段")

    company_df = df[df[company_col] == name]
    if company_df.empty:
        raise HTTPException(status_code=404, detail=f"未找到企业: {name}")

    short_name = company_df[short_col].iloc[0] if short_col in company_df.columns else name
    job_count = len(company_df)
    avg_salary = round(float(company_df['salary_avg'].mean()), 1) if 'salary_avg' in company_df.columns else 0
    city_count = company_df['city'].nunique() if 'city' in company_df.columns else 0
    keyword_count = company_df['keyword'].nunique() if 'keyword' in company_df.columns else 0

    # 岗位类别分布
    keywords = {}
    if 'keyword' in company_df.columns:
        kw_counts = company_df['keyword'].value_counts().head(10)
        keywords = {k: int(v) for k, v in kw_counts.items()}

    # 城市分布
    cities = {}
    if 'city' in company_df.columns:
        city_counts = company_df['city'].value_counts().head(10)
        cities = {k: int(v) for k, v in city_counts.items()}

    # 学历要求
    education = {}
    if 'education' in company_df.columns:
        edu_counts = company_df['education'].value_counts()
        education = {k: int(v) for k, v in edu_counts.items()}

    # 薪资分布
    salary_distribution = {}
    if 'salary_avg' in company_df.columns:
        salary_data = company_df['salary_avg'].dropna()
        if len(salary_data) > 0:
            bins = [0, 10, 15, 20, 25, 30, 40, 50, 100]
            labels = ['<10K', '10-15K', '15-20K', '20-25K', '25-30K', '30-40K', '40-50K', '>50K']
            salary_binned = pd.cut(salary_data, bins=bins, labels=labels)
            salary_counts = salary_binned.value_counts().sort_index()
            salary_distribution = {str(k): int(v) for k, v in salary_counts.items()}

    # 经验要求
    experience = {}
    exp_col = 'workYear' if 'workYear' in company_df.columns else 'work_year'
    if exp_col in company_df.columns:
        exp_counts = company_df[exp_col].value_counts()
        experience = {k: int(v) for k, v in exp_counts.items()}

    # 行业领域
    industries = {}
    ind_col = 'industryField' if 'industryField' in company_df.columns else 'industry_field'
    if ind_col in company_df.columns:
        inds = company_df[ind_col].dropna().str.split(',').explode().str.strip()
        ind_counts = inds.value_counts().head(8)
        industries = {k: int(v) for k, v in ind_counts.items()}

    # 岗位列表
    jobs = []
    display_cols = ['positionName', 'city', 'salary', 'education', 'workYear', 'keyword']
    available_cols = [c for c in display_cols if c in company_df.columns]
    for _, row in company_df[available_cols].iterrows():
        item = {}
        for col in available_cols:
            val = row[col]
            if hasattr(val, 'item'):
                val = val.item()
            item[col] = val
        jobs.append(item)

    return ApiResponse(data=CompanyProfile(
        name=name,
        short_name=str(short_name),
        job_count=job_count,
        avg_salary=avg_salary,
        city_count=city_count,
        keyword_count=keyword_count,
        keywords=keywords,
        cities=cities,
        education=education,
        salary_distribution=salary_distribution,
        experience=experience,
        industries=industries,
        jobs=jobs,
    ).model_dump())
