"""
招聘数据智能分析系统 —— 主入口
基于 Streamlit st.navigation 路由架构，统一管控侧边栏与页面跳转。
运行方式: streamlit run app/main.py
"""
import streamlit as st
import sys
import os
import matplotlib.pyplot as plt

# 将项目根目录加入 Python 路径，确保 src 包可被导入
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 初始化登录状态（必须在 set_page_config 之前判断）
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''

# 页面配置（必须是第一个 Streamlit 命令）
st.set_page_config(
    page_title="招聘数据智能分析系统",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed" if not st.session_state['logged_in'] else "expanded",
)

# ============ 全局 CSS ============
BASE_CSS = """
<style>
    .stApp {
        background-color: #f8f9fc;
        font-family: 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        box-shadow: 2px 0 10px rgba(0,0,0,0.03);
    }
    /* 核心增强：美化 Page Link，让其呈现卡片悬浮高亮效果 */
    [data-testid="stSidebar"] a[data-testid="stPageLink-Link"] {
        background-color: #f8fafc;
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 8px;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid #f1f5f9;
        text-decoration: none !important;
        display: flex;
        align-items: center;
    }
    [data-testid="stSidebar"] a[data-testid="stPageLink-Link"]:hover {
        background-color: #f0f4ff;
        border-color: #4e73df;
        transform: translateX(4px);
        box-shadow: 0 4px 12px rgba(78, 115, 223, 0.08);
    }
    [data-testid="stSidebar"] a[data-testid="stPageLink-Link"]:hover span {
        color: #224abe !important;
    }
    h1, h2, h3 { color: #2b3a4a; font-weight: 600; }
    div[data-testid="metric-container"] {
        background-color: white;
        border-radius: 10px;
        padding: 15px 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.04);
        border-left: 5px solid #4e73df;
        transition: transform 0.2s ease;
    }
    div[data-testid="metric-container"]:hover { transform: translateY(-3px); }
    .stButton>button {
        background-color: #ffffff;
        color: #4e73df;
        border: 1px solid #e0e6ed;
        border-radius: 20px;
        padding: 0.4rem 1rem;
        font-size: 0.9rem;
        transition: all 0.2s ease;
        box-shadow: none;
    }
    .stButton>button:hover {
        border-color: #4e73df;
        background-color: #f8faff;
        color: #224abe;
        transform: translateY(-1px);
    }
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #4e73df, #224abe);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        box-shadow: 0 4px 6px rgba(78, 115, 223, 0.2);
    }
    .stButton>button[kind="primary"]:hover {
        box-shadow: 0 6px 12px rgba(78, 115, 223, 0.4);
    }
    .stDecoration {display: none;}
    #MainMenu {visibility: hidden;}
    button[data-testid="stDeployButton"] {display: none;}
</style>
"""
st.markdown(BASE_CSS, unsafe_allow_html=True)

# 未登录时隐藏侧边栏
if not st.session_state['logged_in']:
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none; }
        [data-testid="stSidebarCollapsedControl"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# ============ 登录验证 ============
from app.components.auth import check_login
check_login()

# ============ 页面视图函数定义 ============

def page_home():
    """🏠 系统首页"""
    st.title("💼 招聘数据智能分析系统")
    st.markdown("""
    ### 欢迎使用招聘数据智能分析系统！

    本系统基于拉勾网 29,500 条真实招聘数据，为您提供深入的招聘市场洞察：

    - **📊 数据可视化大屏**：薪资分布、城市薪酬对比、学历门槛、经验薪资关联等 5 大核心图表
    - **☁️ 岗位词云与需求**：通过 NLP 技术提取技能热词，洞察市场风向
    - **🧠 机器学习聚类分析**：利用 K-Means 算法对岗位进行智能分类
    - **🤖 AI 智能求职助手**：基于通义千问大模型的定制化求职建议

    👈 请从左侧边栏选择功能模块开始体验。
    """)
    from src.data_pipeline.cleaner import load_processed_data
    df = load_processed_data()
    if df is not None and not df.empty:
        st.write("---")
        st.subheader("📋 数据概览")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("📥 总岗位数", f"{len(df):,}")
        with c2:
            if 'salary_avg' in df.columns:
                st.metric("💰 平均薪资", f"{df['salary_avg'].mean():.1f} K")
        with c3:
            if 'city' in df.columns:
                st.metric("🏙️ 覆盖城市", f"{df['city'].nunique()}")
        with c4:
            if 'companyFullName' in df.columns:
                st.metric("🏢 企业数量", f"{df['companyFullName'].nunique():,}")


def page_visualization():
    """📊 数据可视化大屏"""
    from src.data_pipeline.cleaner import load_processed_data, load_count_positions
    from src.visualization import visualization as viz

    st.header("📈 招聘数据商业看板")
    st.markdown("<p style='color:#6c757d;'>基于拉勾网 29,500 条真实数据的多维深度分析报表</p>", unsafe_allow_html=True)
    st.write("---")

    df = load_processed_data()
    count_df = load_count_positions()

    if df is None or df.empty:
        st.error("⚠️ 未找到清洗后的数据！请先运行数据清洗脚本：`python -m src.data_pipeline.cleaner`")
        st.stop()

    # 核心指标卡片
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

    # 图表区域（2 列）
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("### 💸 全行业薪资分布")
        if 'salary_avg' in df.columns:
            st.pyplot(viz.plot_salary_distribution(df))
        st.markdown("### 🎓 学历准入门槛")
        if 'education' in df.columns:
            st.pyplot(viz.plot_education_pie(df))
    with col_right:
        st.markdown("### 🏙️ 一二线城市薪酬对比")
        if 'salary_avg' in df.columns and 'city' in df.columns:
            st.pyplot(viz.plot_city_salary(df))
        st.markdown("### 🔥 热门岗位需求 Top 20")
        if count_df is not None and not count_df.empty:
            st.pyplot(viz.plot_position_demand(count_df, top_n=20))

    # 图表5：跨列展示
    st.write("---")
    st.markdown("### 📈 职场成长路径：工作经验与薪资关联分析")
    st.caption("展示不同工作年限对于薪酬待遇的拉动作用及分布区间。")
    if 'workYear' in df.columns and 'salary_avg' in df.columns:
        st.pyplot(viz.plot_experience_salary(df))


def page_wordcloud():
    """☁️ 岗位词云与需求"""
    from src.data_pipeline.cleaner import load_processed_data
    from src.visualization import visualization as viz

    st.header("☁️ 岗位词云与需求分析")
    st.markdown("<p style='color:#6c757d;'>基于 NLP 分词技术，提取岗位描述与职位名称中的高频技能热词</p>", unsafe_allow_html=True)
    st.write("---")

    df = load_processed_data()
    if df is None or df.empty:
        st.error("⚠️ 未找到清洗后的数据！")
        st.stop()

    st.markdown("### 🌟 核心技能需求画像")
    st.caption("词语越大，在招聘JD中出现的频率越高，反映市场对该技能的旺盛需求。")
    sample_size = st.slider("采样条数（条数越多词云越丰富，但生成越慢）", 500, 5000, 2000, step=500)
    sample_df = df.sample(min(sample_size, len(df)), random_state=42)
    with st.spinner("正在进行 NLP 分词与词云生成..."):
        fig = viz.generate_wordcloud(sample_df, max_words=200)
        st.pyplot(fig)

    st.write("---")
    st.markdown("### 🏙️ 各城市岗位需求量")
    if 'city' in df.columns:
        city_counts = df['city'].value_counts().head(15)
        st.bar_chart(city_counts)

    st.write("---")
    st.markdown("### 🏢 行业领域分布")
    if 'industryField' in df.columns:
        industries = df['industryField'].dropna().str.split(',').explode().str.strip()
        industry_counts = industries.value_counts().head(15)
        st.bar_chart(industry_counts)


def page_ml():
    """🧠 机器学习聚类分析"""
    from src.data_pipeline.cleaner import load_processed_data
    from src.ml_engine.cluster import perform_kmeans_clustering
    from src.ml_engine.classifier import train_classification_model, predict_job_category

    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False

    st.header("🧠 NLP 文本挖掘与岗位预测")
    df = load_processed_data()
    if df is None or df.empty:
        st.error("⚠️ 未找到清洗后的数据！")
        st.stop()

    tab1, tab2 = st.tabs(["🎯 K-Means 岗位聚类分析", "🔮 岗位分类预测引擎"])

    with tab1:
        st.markdown("#### 基于 TF-IDF 与 K-Means 的招聘描述无监督聚类")
        st.caption("算法自动阅读岗位描述文本，将语义相近的岗位归为若干职能簇。")
        n_clusters = st.slider("选择聚类数 K", min_value=3, max_value=10, value=5, step=1)
        if st.button("⚙️ 开始执行 K-Means 聚类", type="primary"):
            with st.spinner("NLP 引擎正在提取特征并训练无监督模型（约需 15-30 秒）..."):
                clustered_df, keywords = perform_kmeans_clustering(df, n_clusters=n_clusters)
                st.success("🎉 聚类分析完成！")
                st.markdown("##### 📌 各职能簇核心特征词画像：")
                for k, v in keywords.items():
                    st.info(f"**簇群 {k}** 核心技能：{v}")
                st.markdown("##### 🗺️ PCA 降维可视化：")
                fig, ax = plt.subplots(figsize=(10, 6))
                scatter = ax.scatter(
                    clustered_df['pca_x'], clustered_df['pca_y'],
                    c=clustered_df['cluster'], cmap='Set2', alpha=0.6, s=15
                )
                ax.set_xlabel('PCA 维度 1')
                ax.set_ylabel('PCA 维度 2')
                ax.set_title('K-Means 聚类结果（PCA 降维投影）')
                plt.colorbar(scatter, label='聚类簇')
                plt.tight_layout()
                st.pyplot(fig)
                st.markdown("##### 📄 部分聚类结果预览：")
                display_cols = ['positionName', 'city', 'salary', 'workYear', 'cluster']
                available_cols = [c for c in display_cols if c in clustered_df.columns]
                st.dataframe(clustered_df[available_cols].head(15), use_container_width=True)

    with tab2:
        st.markdown("#### 朴素贝叶斯岗位智能分类器")
        st.caption("基于岗位描述文本特征，预测该岗位属于哪个关键字类别（如 JAVA、PYTHON、前端工程师等）。")
        if st.button("🔄 训练分类预测模型", type="primary"):
            with st.spinner("正在训练朴素贝叶斯文本分类器（约需 10 秒）..."):
                acc, model, vectorizer, report = train_classification_model(df)
                st.success(f"✅ 模型训练完毕！测试集准确率：**{acc:.2%}**")
                st.session_state['clf_model'] = model
                st.session_state['clf_vec'] = vectorizer
                with st.expander("📊 查看详细分类报告"):
                    st.code(report)
        if 'clf_model' in st.session_state:
            st.write("---")
            test_desc = st.text_area(
                "请在这里粘贴一段真实的岗位描述：",
                "熟练掌握深度学习框架（PyTorch/TensorFlow），有NLP项目落地经验，能阅读最新顶会论文并复现优先。"
            )
            if st.button("🔍 立即预测", type="primary"):
                pred = predict_job_category(test_desc, st.session_state['clf_model'], st.session_state['clf_vec'])
                st.success(f"✨ **预测结果：** 系统判断该岗位最可能属于 **【{pred}】** 类别！")


def page_ai_assistant():
    """🤖 智能求职助手"""
    from src.llm_service.chat_api import chat_with_llm
    from src.llm_service.prompts import get_random_prompts

    st.header("🤖 求职专属大模型 AI 顾问")
    st.markdown(
        "<p style='color:#6c757d;'>基于通义千问强大的语义理解，为您提供简历修改、岗位选择、面试准备等定制化求职建议。</p>",
        unsafe_allow_html=True
    )
    st.write("---")

    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []
    if 'ai_quick_prompts' not in st.session_state:
        st.session_state['ai_quick_prompts'] = get_random_prompts(2)

    for msg in st.session_state['chat_history']:
        avatar = "🧑‍💻" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    prompt = None
    st.markdown(
        "<p style='color:#6c757d; font-size: 0.9em; margin-bottom: 2px;'>💡 猜你想问：</p>",
        unsafe_allow_html=True
    )
    p1, p2 = st.session_state['ai_quick_prompts']
    c1, c2, _ = st.columns([len(p1) + 5, len(p2) + 5, 40])
    with c1:
        if st.button(f"💬 {p1}", type="secondary", use_container_width=False):
            prompt = p1
    with c2:
        if st.button(f"💬 {p2}", type="secondary", use_container_width=False):
            prompt = p2

    if chat_val := st.chat_input("向AI智能顾问提问您的职场疑惑..."):
        prompt = chat_val

    if prompt:
        st.session_state['chat_history'].append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("AI 顾问正在思考中..."):
                response = chat_with_llm(prompt, st.session_state['chat_history'][:-1])
                st.markdown(response)
                st.session_state['chat_history'].append({"role": "assistant", "content": response})


# ============ 路由注册（全部使用函数，避免中文文件名编码问题） ============
page_home_obj = st.Page(page_home, title="系统首页", icon="🏠", default=True)
page_vis_obj = st.Page(page_visualization, title="数据可视化大屏", icon="📊")
page_wc_obj = st.Page(page_wordcloud, title="岗位词云与需求", icon="☁️")
page_ml_obj = st.Page(page_ml, title="机器学习聚类分析", icon="🧠")
page_ai_obj = st.Page(page_ai_assistant, title="智能求职助手", icon="🤖")

# 隐藏默认的自动导航栏，通过 position="hidden" 实现
pg = st.navigation(
    [page_home_obj, page_vis_obj, page_wc_obj, page_ml_obj, page_ai_obj], 
    position="hidden"
)

# ============ 自定义侧边栏（精装商业美化版） ============
# 1. 顶部渐变系统 Logo 徽章
st.sidebar.markdown(
    """
    <div style='background: linear-gradient(135deg, #4e73df, #224abe); border-radius: 12px; padding: 16px; text-align: center; margin-top: 25px; margin-bottom: 30px; box-shadow: 0 4px 12px rgba(78,115,223,0.15);'>
        <div style='font-size: 1.25rem; font-weight: 800; color: white; letter-spacing: 1px;'>💼 RECRUIT AI</div>
        <div style='font-size: 0.8rem; color: rgba(255,255,255,0.85); margin-top: 3px;'>招聘数据智能分析系统</div>
    </div>
    """,
    unsafe_allow_html=True
)

# 2. 用户身份信息展示卡片
username = st.session_state.get('username', '')
st.sidebar.markdown(
    f"""
    <div style='background-color: #f8fafc; border-radius: 10px; padding: 12px; border: 1px solid #edf2f7; margin-bottom: 35px; display: flex; align-items: center;'>
        <div style='font-size: 1.5rem; margin-right: 10px;'>👤</div>
        <div>
            <div style='font-size: 0.75rem; color: #718096;'>当前登录用户</div>
            <div style='font-size: 0.95rem; font-weight: bold; color: #2d3748;'>{username}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# 3. 页面导航菜单
st.sidebar.page_link(page_home_obj)
st.sidebar.page_link(page_vis_obj)
st.sidebar.page_link(page_wc_obj)
st.sidebar.page_link(page_ml_obj)
st.sidebar.page_link(page_ai_obj)

# 4. 中部系统状态卡片（充实空白空间）
st.sidebar.markdown(
    """
    <div style='margin-top: 25px; margin-bottom: 8px; font-size: 0.75rem; font-weight: bold; color: #a0aec0; letter-spacing: 0.5px;'>📊 系统运行状态</div>
    <div style='background-color: #f8fafc; border-radius: 10px; padding: 12px; border: 1px solid #edf2f7; margin-bottom: 15px;'>
        <div style='display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 6px;'>
            <span style='color: #718096;'>数据规模:</span>
            <span style='font-weight: bold; color: #2d3748;'>29,500 条</span>
        </div>
        <div style='display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 6px;'>
            <span style='color: #718096;'>系统版本:</span>
            <span style='font-weight: bold; color: #2d3748;'>v1.0.2 Stable</span>
        </div>
        <div style='display: flex; justify-content: space-between; font-size: 0.8rem;'>
            <span style='color: #718096;'>NLP 引擎:</span>
            <span style='font-weight: bold; color: #48bb78;'>🟢 运行正常</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# 弹性间距，将退出按钮推至最底
st.sidebar.markdown("<div style='height: 18vh;'></div>", unsafe_allow_html=True)

# 5. 退出登录按钮
st.sidebar.divider()
if st.sidebar.button("🚪 退出登录", use_container_width=True):
    st.session_state['logged_in'] = False
    st.session_state['username'] = ''
    st.rerun()

# 运行当前路由页面
pg.run()
