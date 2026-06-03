"""数据接口路由 - 数据概览、岗位列表、筛选选项"""
from typing import Optional
from fastapi import APIRouter, Depends, Query

from backend.dependencies import get_data_df, get_current_user
from backend.schemas.models import OverviewStats, ApiResponse

router = APIRouter(prefix="/api/data", tags=["数据接口"])


@router.get("/overview", response_model=ApiResponse)
def get_overview():
    """返回数据概览统计"""
    df = get_data_df()
    if df is None or df.empty:
        return ApiResponse(data=OverviewStats(
            total_jobs=0, avg_salary=0, city_count=0, company_count=0, keyword_count=0
        ).model_dump())

    total_jobs = len(df)
    avg_salary = round(df['salary_avg'].mean(), 1) if 'salary_avg' in df.columns else 0
    city_count = df['city'].nunique() if 'city' in df.columns else 0
    company_col = 'companyFullName' if 'companyFullName' in df.columns else 'company_full_name'
    company_count = df[company_col].nunique() if company_col in df.columns else 0
    keyword_count = df['keyword'].nunique() if 'keyword' in df.columns else 0

    return ApiResponse(data=OverviewStats(
        total_jobs=total_jobs,
        avg_salary=avg_salary,
        city_count=city_count,
        company_count=company_count,
        keyword_count=keyword_count,
    ).model_dump())


@router.get("/jobs", response_model=ApiResponse)
def get_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    city: Optional[str] = None,
    keyword: Optional[str] = None,
    education: Optional[str] = None,
    work_year: Optional[str] = None,
    username: str = Depends(get_current_user),
):
    """返回岗位列表（支持分页和筛选）"""
    df = get_data_df(city=city, keyword=keyword, education=education, work_year=work_year)
    if df is None or df.empty:
        return ApiResponse(data={"items": [], "total": 0, "page": page, "page_size": page_size})

    total = len(df)
    start = (page - 1) * page_size
    end = start + page_size
    page_df = df.iloc[start:end]

    # 统一列名输出
    col_map = {
        'positionName': 'position_name',
        'companyFullName': 'company_full_name',
        'companyShortName': 'company_short_name',
        'companySize': 'company_size',
        'industryField': 'industry_field',
        'financeStage': 'finance_stage',
        'positionDetail': 'position_detail',
        'positionAdvantage': 'position_advantage',
        'workYear': 'work_year',
    }

    items = []
    for _, row in page_df.iterrows():
        item = {}
        for col in df.columns:
            key = col_map.get(col, col)
            val = row[col]
            if hasattr(val, 'item'):
                val = val.item()
            item[key] = val
        items.append(item)

    return ApiResponse(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/filters", response_model=ApiResponse)
def get_filters(username: str = Depends(get_current_user)):
    """返回可用的筛选选项"""
    df = get_data_df()
    if df is None or df.empty:
        return ApiResponse(data={"cities": [], "keywords": [], "educations": [], "work_years": []})

    cities = sorted(df['city'].dropna().unique().tolist()) if 'city' in df.columns else []
    keywords = sorted(df['keyword'].dropna().unique().tolist()) if 'keyword' in df.columns else []
    educations = sorted(df['education'].dropna().unique().tolist()) if 'education' in df.columns else []

    work_year_col = 'workYear' if 'workYear' in df.columns else 'work_year'
    work_years = sorted(df[work_year_col].dropna().unique().tolist()) if work_year_col in df.columns else []

    return ApiResponse(data={
        "cities": cities,
        "keywords": keywords,
        "educations": educations,
        "work_years": work_years,
    })
