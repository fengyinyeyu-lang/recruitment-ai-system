"""报告导出路由 - 生成 HTML 分析报告"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_data_df, get_current_user
from backend.schemas.models import ReportRequest, ReportResponse, ApiResponse

router = APIRouter(prefix="/api/report", tags=["报告导出"])


@router.post("/generate", response_model=ApiResponse)
def generate_report(req: ReportRequest, username: str = Depends(get_current_user)):
    """生成 HTML 报告，返回 HTML 内容和文件名"""
    import pandas as pd

    df = get_data_df()
    if df is None or df.empty:
        raise HTTPException(status_code=400, detail="暂无数据，无法生成报告")

    # 过滤数据（支持模糊匹配：前端传"北京"也能匹配数据库中的"北京市"）
    report_df = df.copy()
    if req.city != "全国" and 'city' in df.columns:
        report_df = report_df[report_df['city'].str.contains(req.city, na=False)]
    if req.keyword != "全部岗位" and 'keyword' in df.columns:
        report_df = report_df[report_df['keyword'].str.contains(req.keyword, na=False)]

    if report_df.empty:
        raise HTTPException(status_code=400, detail="筛选条件下无数据")

    # 统计数据
    total = len(report_df)
    avg_salary = report_df['salary_avg'].mean() if 'salary_avg' in report_df.columns else 0
    city_count = report_df['city'].nunique() if 'city' in report_df.columns else 0
    company_col = 'companyFullName' if 'companyFullName' in report_df.columns else 'company_full_name'
    company_count = report_df[company_col].nunique() if company_col in report_df.columns else 0
    kw_count = report_df['keyword'].nunique() if 'keyword' in report_df.columns else 0

    # Top 城市薪资
    city_salary_html = ""
    cs = None
    if 'city' in report_df.columns and 'salary_avg' in report_df.columns:
        cs = report_df.groupby('city')['salary_avg'].mean().sort_values(ascending=False).head(10)
        city_salary_html = "<table><tr><th>城市</th><th>平均薪资(K)</th></tr>"
        for city, sal in cs.items():
            city_salary_html += f"<tr><td>{city}</td><td>{sal:.1f}K</td></tr>"
        city_salary_html += "</table>"

    # Top 岗位需求
    demand_html = ""
    dem = None
    if 'keyword' in report_df.columns:
        dem = report_df['keyword'].value_counts().head(15)
        demand_html = "<table><tr><th>岗位类别</th><th>需求数量</th></tr>"
        for kw, cnt in dem.items():
            demand_html += f"<tr><td>{kw}</td><td>{cnt}</td></tr>"
        demand_html += "</table>"

    # 学历分布
    edu_html = ""
    if 'education' in report_df.columns:
        edu = report_df['education'].value_counts()
        edu_html = "<table><tr><th>学历</th><th>占比</th></tr>"
        for e, c in edu.items():
            edu_html += f"<tr><td>{e}</td><td>{c}/{total} ({c/total*100:.1f}%)</td></tr>"
        edu_html += "</table>"

    # 薪资分布区间
    salary_dist_html = ""
    if 'salary_avg' in report_df.columns:
        bins = [0, 10, 15, 20, 25, 30, 40, 50, 100]
        labels = ['<10K', '10-15K', '15-20K', '20-25K', '25-30K', '30-40K', '40-50K', '>50K']
        report_df_copy = report_df.copy()
        report_df_copy['salary_bin'] = pd.cut(report_df_copy['salary_avg'], bins=bins, labels=labels)
        sd = report_df_copy['salary_bin'].value_counts().sort_index()
        salary_dist_html = "<table><tr><th>薪资区间</th><th>岗位数</th></tr>"
        for b, c in sd.items():
            salary_dist_html += f"<tr><td>{b}</td><td>{c}</td></tr>"
        salary_dist_html += "</table>"

    # 完整 HTML
    title = "招聘数据分析报告"
    subtitle = f"分析范围: {req.city} | {req.keyword} | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif; background: #f8f9fc; color: #2b3a4a; }}
    .header {{ background: linear-gradient(135deg, #4e73df, #224abe); color: white; padding: 40px 50px; border-radius: 0 0 20px 20px; }}
    .header h1 {{ font-size: 2rem; margin-bottom: 8px; }}
    .header p {{ opacity: 0.9; font-size: 1rem; }}
    .container {{ max-width: 1000px; margin: 0 auto; padding: 30px 20px; }}
    .section {{ background: white; border-radius: 12px; padding: 24px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.04); }}
    .section h2 {{ color: #4e73df; font-size: 1.3rem; margin-bottom: 16px; border-left: 4px solid #4e73df; padding-left: 12px; }}
    .metrics {{ display: flex; gap: 16px; flex-wrap: wrap; }}
    .metric {{ flex: 1; min-width: 150px; background: #f8fafc; border-radius: 10px; padding: 16px; text-align: center; }}
    .metric .value {{ font-size: 1.8rem; font-weight: 700; color: #4e73df; }}
    .metric .label {{ font-size: 0.85rem; color: #858796; margin-top: 4px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
    th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid #edf2f7; font-size: 0.9rem; }}
    th {{ background: #f8fafc; color: #4e73df; font-weight: 600; }}
    tr:hover td {{ background: #f8faff; }}
    .footer {{ text-align: center; color: #858796; font-size: 0.85rem; padding: 30px; }}
</style>
</head>
<body>
<div class="header">
    <h1>📊 {title}</h1>
    <p>{subtitle}</p>
    <p style="margin-top:8px;">生成用户: {username}</p>
</div>
<div class="container">

    <div class="section">
        <h2>📈 核心数据指标</h2>
        <div class="metrics">
            <div class="metric"><div class="value">{total:,}</div><div class="label">岗位总数</div></div>
            <div class="metric"><div class="value">{avg_salary:.1f}K</div><div class="label">平均薪资</div></div>
            <div class="metric"><div class="value">{city_count}</div><div class="label">覆盖城市</div></div>
            <div class="metric"><div class="value">{company_count:,}</div><div class="label">企业数量</div></div>
            <div class="metric"><div class="value">{kw_count}</div><div class="label">岗位类别</div></div>
        </div>
    </div>

    <div class="section">
        <h2>🏙️ 城市薪资排行 Top 10</h2>
        {city_salary_html}
    </div>

    <div class="section">
        <h2>🔥 热门岗位需求 Top 15</h2>
        {demand_html}
    </div>

    <div class="section">
        <h2>🎓 学历要求分布</h2>
        {edu_html}
    </div>

    <div class="section">
        <h2>💰 薪资区间分布</h2>
        {salary_dist_html}
    </div>

    <div class="section">
        <h2>💡 分析洞察与建议</h2>
        <ul style="padding-left:20px; line-height:2; color:#555;">
            <li>📊 本次分析覆盖 <b>{total:,}</b> 条岗位数据，平均薪资 <b>{avg_salary:.1f}K</b></li>
            <li>🏙️ 薪资最高城市为 <b>{cs.index[0] if cs is not None and len(cs) > 0 else "N/A"}</b>，平均 <b>{cs.iloc[0]:.1f}K</b></li>
            <li>🔥 需求量最大的岗位类别为 <b>{dem.index[0] if dem is not None and len(dem) > 0 else "N/A"}</b></li>
            <li>📈 建议求职者关注高薪赛道，同时结合自身技能选择匹配度高的岗位</li>
        </ul>
    </div>

    <div class="footer">
        <p>📋 由招聘数据智能分析系统自动生成 | {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        <p style="margin-top:6px;">系统版本 v2.0 Pro | 数据源自主流招聘平台</p>
    </div>

</div>
</body>
</html>"""

    filename = f"招聘分析报告_{datetime.now().strftime('%Y%m%d_%H%M')}.html"

    return ApiResponse(data=ReportResponse(
        html_content=html_content,
        filename=filename,
    ).model_dump())
