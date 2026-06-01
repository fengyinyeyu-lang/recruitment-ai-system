"""
页面1：📊 数据可视化大屏
展示 5 个核心可视化图表，所有绘图逻辑均来自 src.visualization.visualization
"""
import streamlit as st
import sys
import os

# 路径配置
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.components.auth import check_login
check_login()

from src.data_pipeline.cleaner import load_processed_data, load_count_positions
from src.visualization import visualization as viz

st.session_state['last_active_page'] = 'visualization'

# ========== 页面专属样式 ==========
st.markdown("""
<style>
    /* 渐变 Banner 标题栏 */
    .dashboard-banner {
        background: linear-gradient(135deg, #4e73df 0%, #224abe 50%, #1a3a9e 100%);
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 24px;
        box-shadow: 0 8px 24px rgba(78, 115, 223, 0.2);
        position: relative;
        overflow: hidden;
    }
    .dashboard-banner::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
        border-radius: 50%;
    }
    .dashboard-banner h1 {
        color: white !important;
        margin: 0;
        font-size: 1.75rem;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .dashboard-banner p {
        color: rgba(255,255,255,0.8) !important;
        margin: 8px 0 0 0;
        font-size: 0.95rem;
    }

    /* 指标卡片 */
    .metric-card {
        background: white;
        border-radius: 14px;
        padding: 20px 22px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.05);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid #f0f0f5;
        position: relative;
        overflow: hidden;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    .metric-card .metric-icon {
        font-size: 1.6rem;
        margin-bottom: 6px;
    }
    .metric-card .metric-label {
        font-size: 0.8rem;
        color: #858796;
        font-weight: 500;
        margin-bottom: 4px;
    }
    .metric-card .metric-value {
        font-size: 1.65rem;
        font-weight: 700;
        color: #2b3a4a;
        line-height: 1.2;
    }
    .metric-card .metric-delta {
        font-size: 0.75rem;
        color: #1cc88a;
        margin-top: 4px;
        font-weight: 500;
    }
    .metric-card .metric-bar {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
    }
    .bar-blue   { background: linear-gradient(90deg, #4e73df, #36b9cc); }
    .bar-green  { background: linear-gradient(90deg, #1cc88a, #36b9cc); }
    .bar-orange { background: linear-gradient(90deg, #f6c23e, #e74a3b); }
    .bar-purple { background: linear-gradient(90deg, #764ba2, #4e73df); }

    /* 图表展示容器 */
    .chart-container {
        background: white;
        border-radius: 14px;
        padding: 28px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04);
        border: 1px solid #f0f0f5;
        margin-top: 8px;
    }
    .chart-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #2b3a4a;
        margin-bottom: 4px;
    }
    .chart-subtitle {
        font-size: 0.85rem;
        color: #858796;
        margin-bottom: 16px;
    }

    /* 选项卡导航增强 */
    div[data-testid="stRadio"] > div[role="radiogroup"] > label {
        background-color: #f8f9fc;
        border: 1.5px solid #e8ecf1;
        border-radius: 12px;
        padding: 10px 20px;
        margin-right: 10px;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        font-weight: 500;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
        background-color: #eef2ff;
        border-color: #4e73df;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(78, 115, 223, 0.12);
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label[data-baseweb="radio"]:has(input:checked) {
        background: linear-gradient(135deg, #4e73df, #224abe);
        border-color: #4e73df;
        color: white;
        box-shadow: 0 4px 15px rgba(78, 115, 223, 0.3);
        transform: translateY(-2px);
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label[data-baseweb="radio"]:has(input:checked) div {
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ========== 渐变 Banner 标题 ==========
st.markdown("""
<div class='dashboard-banner'>
    <h1>📈 招聘数据商业看板</h1>
    <p>基于拉勾网 29,500 条真实数据的多维深度分析报表</p>
</div>
""", unsafe_allow_html=True)

# 加载数据
df = load_processed_data()
count_df = load_count_positions()

if df is None or df.empty:
    st.error("⚠️ 未找到清洗后的数据！请先运行数据清洗脚本：`python src/data_pipeline/cleaner.py`")
    st.stop()

# ========== 核心指标卡片（自定义 HTML） ==========
total_positions = f"{len(df):,}"
avg_salary = f"{df['salary_avg'].mean():.1f} K" if 'salary_avg' in df.columns else "--"
company_count = f"{df['companyFullName'].nunique():,}" if 'companyFullName' in df.columns else "--"
keyword_count = f"{df['keyword'].nunique()}" if 'keyword' in df.columns else "--"

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-bar bar-blue'></div>
        <div class='metric-icon'>📥</div>
        <div class='metric-label'>采集总岗位数</div>
        <div class='metric-value'>{total_positions}</div>
        <div class='metric-delta'>▲ 实时更新</div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-bar bar-green'></div>
        <div class='metric-icon'>💰</div>
        <div class='metric-label'>行业平均薪资</div>
        <div class='metric-value'>{avg_salary}</div>
        <div class='metric-delta'>月薪中位数</div>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-bar bar-orange'></div>
        <div class='metric-icon'>🏢</div>
        <div class='metric-label'>覆盖企业数量</div>
        <div class='metric-value'>{company_count}</div>
        <div class='metric-delta'>多行业覆盖</div>
    </div>
    """, unsafe_allow_html=True)
with c4:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-bar bar-purple'></div>
        <div class='metric-icon'>🔥</div>
        <div class='metric-label'>热门岗位类别</div>
        <div class='metric-value'>{keyword_count}</div>
        <div class='metric-delta'>技术方向</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# ========== 图表路由导航 ==========
CHART_OPTIONS = {
    "💸 薪资分布": "salary",
    "🏙️ 城市薪酬": "city",
    "🎓 学历门槛": "education",
    "🔥 岗位需求": "demand",
    "📈 经验薪资": "experience",
}

selected = st.radio(
    "选择图表",
    options=list(CHART_OPTIONS.keys()),
    horizontal=True,
    label_visibility="collapsed",
)
chart_key = CHART_OPTIONS[selected]

# ========== 图表元信息映射 ==========
CHART_META = {
    "salary":     {"title": "💸 全行业薪资分布",   "desc": "展示所有岗位的平均月薪分布直方图与核密度估计曲线"},
    "city":       {"title": "🏙️ 一二线城市薪酬对比", "desc": "对比各城市平均薪资水平，揭示地域薪酬差异"},
    "education":  {"title": "🎓 学历准入门槛",     "desc": "分析不同学历要求的岗位占比，洞察学历门槛分布"},
    "demand":     {"title": "🔥 热门岗位需求 Top 20", "desc": "统计各岗位关键字的需求数量，展示最热门的技术方向"},
    "experience": {"title": "📈 工作经验与薪资关联",  "desc": "展示不同工作年限对于薪酬待遇的拉动作用及分布区间"},
}
meta = CHART_META[chart_key]

# ========== 图表展示区（白色卡片容器） ==========
st.markdown(f"""
<div class='chart-container'>
    <div class='chart-title'>{meta['title']}</div>
    <div class='chart-subtitle'>{meta['desc']}</div>
</div>
""", unsafe_allow_html=True)

# ========== 根据选择渲染对应图表 ==========
if chart_key == "salary":
    if 'salary_avg' in df.columns:
        st.pyplot(viz.plot_salary_distribution(df))
    else:
        st.warning("薪资数据未解析，请检查数据清洗流程。")

elif chart_key == "city":
    if 'salary_avg' in df.columns and 'city' in df.columns:
        st.pyplot(viz.plot_city_salary(df))
    else:
        st.warning("城市或薪资数据缺失。")

elif chart_key == "education":
    if 'education' in df.columns:
        st.pyplot(viz.plot_education_pie(df))
    else:
        st.warning("学历数据未解析。")

elif chart_key == "demand":
    if count_df is not None and not count_df.empty:
        st.pyplot(viz.plot_position_demand(count_df, top_n=20))
    else:
        st.info("岗位统计数据暂未生成。")

elif chart_key == "experience":
    if 'workYear' in df.columns and 'salary_avg' in df.columns:
        st.pyplot(viz.plot_experience_salary(df))
    else:
        st.warning("工作经验或薪资数据缺失。")
