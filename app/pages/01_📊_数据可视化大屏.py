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
st.header("📈 招聘数据商业看板")
st.markdown("<p style='color:#6c757d;'>基于拉勾网 29,500 条真实数据的多维深度分析报表</p>", unsafe_allow_html=True)
st.write("---")

# 加载数据
df = load_processed_data()
count_df = load_count_positions()

if df is None or df.empty:
    st.error("⚠️ 未找到清洗后的数据！请先运行数据清洗脚本：`python src/data_pipeline/cleaner.py`")
    st.stop()

# ========== 核心指标卡片 ==========
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric(label="📥 采集总岗位数", value=f"{len(df):,}", delta="实时更新")
with c2:
    if 'salary_avg' in df.columns:
        st.metric(label="💰 行业平均薪资", value=f"{df['salary_avg'].mean():.1f} K")
with c3:
    if 'companyFullName' in df.columns:
        st.metric(label="🏢 覆盖企业数量", value=f"{df['companyFullName'].nunique():,}")
with c4:
    if 'keyword' in df.columns:
        st.metric(label="🔥 热门岗位类别", value=f"{df['keyword'].nunique()}")

st.write("<br>", unsafe_allow_html=True)

# ========== 图表区域（2列布局） ==========
col_left, col_right = st.columns(2)

with col_left:
    # 图表1：薪资分布
    st.markdown("### 💸 全行业薪资分布")
    if 'salary_avg' in df.columns:
        st.pyplot(viz.plot_salary_distribution(df))
    else:
        st.warning("薪资数据未解析，请检查数据清洗流程。")

    # 图表3：学历分布饼图
    st.markdown("### 🎓 学历准入门槛")
    if 'education' in df.columns:
        st.pyplot(viz.plot_education_pie(df))

with col_right:
    # 图表2：城市薪酬对比
    st.markdown("### 🏙️ 一二线城市薪酬对比")
    if 'salary_avg' in df.columns and 'city' in df.columns:
        st.pyplot(viz.plot_city_salary(df))

    # 图表4：岗位需求柱状图
    st.markdown("### 🔥 热门岗位需求 Top 20")
    if count_df is not None and not count_df.empty:
        st.pyplot(viz.plot_position_demand(count_df, top_n=20))
    else:
        st.info("岗位统计数据暂未生成。")

# ========== 图表5：跨列展示 ==========
st.write("---")
st.markdown("### 📈 职场成长路径：工作经验与薪资关联分析")
st.caption("展示不同工作年限对于薪酬待遇的拉动作用及分布区间。")
if 'workYear' in df.columns and 'salary_avg' in df.columns:
    st.pyplot(viz.plot_experience_salary(df))
else:
    st.warning("工作经验或薪资数据缺失。")
