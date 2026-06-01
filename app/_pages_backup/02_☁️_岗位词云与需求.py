"""
页面2：☁️ 岗位词云与需求分析
通过 NLP 技术提取岗位描述中的高频关键词，生成词云图。
"""
import streamlit as st
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.components.auth import check_login
check_login()

from src.data_pipeline.cleaner import load_processed_data
from src.visualization import visualization as viz

st.session_state['last_active_page'] = 'wordcloud'
st.header("☁️ 岗位词云与需求分析")
st.markdown("<p style='color:#6c757d;'>基于 NLP 分词技术，提取岗位描述与职位名称中的高频技能热词</p>", unsafe_allow_html=True)
st.write("---")

df = load_processed_data()

if df is None or df.empty:
    st.error("⚠️ 未找到清洗后的数据！请先运行数据清洗脚本。")
    st.stop()

# ========== 词云生成 ==========
st.markdown("### 🌟 核心技能需求画像")
st.caption("词语越大，在招聘JD中出现的频率越高，反映市场对该技能的旺盛需求。")

# 采样以加速渲染
sample_size = st.slider("采样条数（条数越多词云越丰富，但生成越慢）", 500, 5000, 2000, step=500)
sample_df = df.sample(min(sample_size, len(df)), random_state=42)

with st.spinner("正在进行 NLP 分词与词云生成..."):
    fig = viz.generate_wordcloud(sample_df, max_words=200)
    st.pyplot(fig)

# ========== 城市需求热力展示 ==========
st.write("---")
st.markdown("### 🏙️ 各城市岗位需求量")
if 'city' in df.columns:
    city_counts = df['city'].value_counts().head(15)
    st.pyplot(viz.plot_horizontal_bar(city_counts, "城市招聘岗位需求量 Top 15", "岗位数量"))
else:
    st.info("城市字段缺失。")

# ========== 行业分布 ==========
st.write("---")
st.markdown("### 🏢 行业领域分布")
if 'industryField' in df.columns:
    # 处理行业字段中的逗号分隔
    industries = df['industryField'].dropna().str.split(',').explode().str.strip()
    industry_counts = industries.value_counts().head(15)
    st.pyplot(viz.plot_horizontal_bar(industry_counts, "行业领域分布 Top 15", "岗位数量"))

