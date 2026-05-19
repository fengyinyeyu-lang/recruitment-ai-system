"""
页面3：🧠 机器学习聚类分析
展示 K-Means 无监督聚类结果和朴素贝叶斯分类预测引擎。
"""
import streamlit as st
import sys
import os
import matplotlib.pyplot as plt

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.components.auth import check_login
check_login()

from src.data_pipeline.cleaner import load_processed_data
from src.ml_engine.cluster import perform_kmeans_clustering
from src.ml_engine.classifier import train_classification_model, predict_job_category

# 中文字体配置
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

st.session_state['last_active_page'] = 'ml'
st.header("🧠 NLP 文本挖掘与岗位预测")

df = load_processed_data()
if df is None or df.empty:
    st.error("⚠️ 未找到清洗后的数据！")
    st.stop()

tab1, tab2 = st.tabs(["🎯 K-Means 岗位聚类分析", "🔮 岗位分类预测引擎"])

# ========== Tab1: K-Means 聚类 ==========
with tab1:
    st.markdown("#### 基于 TF-IDF 与 K-Means 的招聘描述无监督聚类")
    st.caption("算法自动阅读岗位描述文本，将语义相近的岗位归为若干职能簇。")

    n_clusters = st.slider("选择聚类数 K", min_value=3, max_value=10, value=5, step=1)

    if st.button("⚙️ 开始执行 K-Means 聚类", type="primary"):
        with st.spinner("NLP 引擎正在提取特征并训练无监督模型（约需 15-30 秒）..."):
            clustered_df, keywords = perform_kmeans_clustering(df, n_clusters=n_clusters)
            st.success("🎉 聚类分析完成！")

            # 展示每个簇的关键词
            st.markdown("##### 📌 各职能簇核心特征词画像：")
            for k, v in keywords.items():
                st.info(f"**簇群 {k}** 核心技能：{v}")

            # PCA 散点图可视化
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

            # 数据预览
            st.markdown("##### 📄 部分聚类结果预览：")
            display_cols = ['positionName', 'city', 'salary', 'workYear', 'cluster']
            available_cols = [c for c in display_cols if c in clustered_df.columns]
            st.dataframe(clustered_df[available_cols].head(15), use_container_width=True)

# ========== Tab2: 分类预测 ==========
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
            pred = predict_job_category(
                test_desc,
                st.session_state['clf_model'],
                st.session_state['clf_vec']
            )
            st.success(f"✨ **预测结果：** 系统判断该岗位最可能属于 **【{pred}】** 类别！")
