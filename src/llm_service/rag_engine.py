"""
RAG Engine - 基于招聘数据的智能客服知识增强模块
使用 DashScope Embedding + 向量检索实现知识增强对话。
"""
import os
import json
import logging
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAG_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "rag_knowledge.json")
EMBEDDING_CACHE_PATH = os.path.join(PROJECT_ROOT, "data", "rag_embeddings.npy")

# ------------------------------------------------------------------
# 知识库构建
# ------------------------------------------------------------------

def build_knowledge_base(csv_path=None):
    """从招聘统计数据中构建结构化RAG知识库。"""
    if csv_path is None:
        csv_path = os.path.join(PROJECT_ROOT, "data", "processed", "cleaned_jobs.csv")
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    knowledge = []
    NL = "\n"

    # 提前初始化通用汇总需要的变量
    master_mean = bachelor_mean = gap_mean = gap_pct = 0.0

    # 辅助函数：兼容新旧列名
    def _col(name_map):
        """传入 {new_name: old_name} 字典，返回 DataFrame 中实际存在的列名，不存在则返回 None"""
        for name in name_map:
            if name in df.columns:
                return name
        return None

    company_col = _col({'company_full_name': 1, 'companyFullName': 1})
    work_year_col = _col({'work_year': 1, 'workYear': 1})
    company_size_col = _col({'company_size': 1, 'companySize': 1})
    position_detail_col = _col({'position_detail': 1, 'positionDetail': 1})

    # 1. 全局概览
    avg_s = df['salary_avg'].mean()
    med_s = df['salary_avg'].median()
    company_count = df[company_col].nunique() if company_col else 0
    knowledge.append({
        "title": "全局招聘市场概览",
        "content": (
            f"本数据库共收录 {len(df)} 条招聘数据，覆盖 {df['city'].nunique()} 个城市、"
            f"{company_count} 家企业、{df['keyword'].nunique()} 个岗位类别。"
            f"全行业平均薪资为 {avg_s:.1f}K，薪资中位数为 {med_s:.1f}K。"
        )
    })

    # 2. 城市薪资排行
    if 'city' in df.columns and 'salary_avg' in df.columns:
        city_sal = df.groupby('city')['salary_avg'].agg(['mean', 'count']).sort_values('mean', ascending=False)
        top_cities = city_sal.head(10)
        city_lines = [f"{idx}: 平均薪资 {row['mean']:.1f}K (共 {row['count']} 条)" for idx, row in top_cities.iterrows()]
        knowledge.append({
            "title": "城市薪资排行 Top10",
            "content": "各城市平均薪资排名（Top 10）：\n" + "\n".join(city_lines)
        })
        # 补充每个热门城市的详细分析
        for idx, row in top_cities.head(5).iterrows():
            city_df = df[df['city'] == idx]
            top_kw = city_df['keyword'].value_counts().head(3)
            kw_str = ", ".join([f"{k}({v}条)" for k, v in top_kw.items()])
            edu_dist = city_df['education'].value_counts().head(3).to_dict()
            edu_str = ", ".join([f"{k}:{v}条" for k, v in edu_dist.items()])
            knowledge.append({
                "title": f"{idx}市招聘市场详情",
                "content": (
                    f"{idx}市平均薪资 {row['mean']:.1f}K，共发布 {row['count']} 条岗位。"
                    f"热门岗位类别：{kw_str}。学历要求分布：{edu_str}。"
                )
            })

    # 3. 岗位类别薪资分析
    if 'keyword' in df.columns:
        kw_sal = df.groupby('keyword')['salary_avg'].agg(['mean', 'count']).sort_values('mean', ascending=False)
        top_kws = kw_sal.head(15)
        kw_lines = [f"{idx}: 平均 {row['mean']:.1f}K (共 {row['count']} 条)" for idx, row in top_kws.iterrows()]
        knowledge.append({
            "title": "热门岗位类别薪资排行 Top15",
            "content": "各岗位类别平均薪资排名：\n" + "\n".join(kw_lines)
        })

    # 4. 学历与薪资关系（增强版：包含硕士vs本科具体差距）
    if 'education' in df.columns:
        edu_sal = df.groupby('education')['salary_avg'].agg(['mean', 'count']).sort_values('mean', ascending=False)
        edu_lines = [f"{idx}: 平均 {row['mean']:.1f}K (共 {row['count']} 条)" for idx, row in edu_sal.iterrows()]
        knowledge.append({
            "title": "不同学历对应的平均薪资",
            "content": "学历与平均薪资关系：\n" + "\n".join(edu_lines)
        })

        # 4.1 硕士与本科薪资对比分析
        edu_values = df['education'].dropna().unique()
        # 标准化学历名称
        def normalize_edu(e):
            e = str(e).strip().replace(" ", "").replace("　", "")
            if e in ["硕士", "硕士及以上", "Master", "master", "硕士以上", "高级以上", "不限以上"]:
                return "硕士及以上"
            elif e in ["本科", "大专及以上", "本科及以上", "Bachelor", "bachelor", "本科以上"]:
                return "本科及以上"
            elif e in ["大专", "大专以上", "专科", "中专"]:
                return "大专及以上"
            elif e in ["不限", "学历不限", "无要求", "不限以下"]:
                return "不限"
            return e
        df['edu_norm'] = df['education'].apply(normalize_edu)

        # 计算硕士vs本科薪资差距
        edu_compare = df.groupby('edu_norm')['salary_avg'].agg(['mean', 'median', 'count'])
        if '硕士及以上' in edu_compare.index and '本科及以上' in edu_compare.index:
            master_mean = edu_compare.loc['硕士及以上', 'mean']
            bachelor_mean = edu_compare.loc['本科及以上', 'mean']
            master_median = edu_compare.loc['硕士及以上', 'median']
            bachelor_median = edu_compare.loc['本科及以上', 'median']
            master_count = int(edu_compare.loc['硕士及以上', 'count'])
            bachelor_count = int(edu_compare.loc['本科及以上', 'count'])
            gap_mean = master_mean - bachelor_mean
            gap_median = master_median - bachelor_median
            gap_pct = (gap_mean / bachelor_mean) * 100 if bachelor_mean > 0 else 0
            knowledge.append({
                "title": "硕士与本科薪资差距分析",
                "content": (
                    f"根据数据库统计分析，硕士学历平均薪资为 {master_mean:.1f}K，"
                    f"本科学历平均薪资为 {bachelor_mean:.1f}K。"
                    f"硕士比本科平均高出 {gap_mean:.1f}K，增幅约 {gap_pct:.1f}%。"
                    f"硕士薪资中位数为 {master_median:.1f}K，本科为 {bachelor_median:.1f}K，"
                    f"中位数差距为 {gap_median:.1f}K。"
                    f"数据库中硕士相关岗位共 {master_count} 条，本科相关岗位共 {bachelor_count} 条。"
                )
            })

        # 4.2 按岗位类别划分的学历薪资对比
        if 'keyword' in df.columns:
            for kw in df['keyword'].value_counts().head(10).index:
                kw_df = df[df['keyword'] == kw]
                kw_edu = kw_df.groupby('edu_norm')['salary_avg'].mean()
                if '硕士及以上' in kw_edu.index and '本科及以上' in kw_edu.index:
                    m = kw_edu['硕士及以上']
                    b = kw_edu['本科及以上']
                    gap = m - b
                    pct = (gap / b) * 100 if b > 0 else 0
                    knowledge.append({
                        "title": f"{kw}岗位硕士与本科薪资对比",
                        "content": (
                            f"{kw}岗位中，硕士平均薪资 {m:.1f}K，"
                            f"本科平均薪资 {b:.1f}K，"
                            f"硕士比本科高 {gap:.1f}K（增幅 {pct:.1f}%）。"
                        )
                    })

        # 4.3 各城市学历薪资对比
        if 'city' in df.columns:
            for city in df['city'].value_counts().head(5).index:
                city_df = df[df['city'] == city]
                city_edu = city_df.groupby('edu_norm')['salary_avg'].mean()
                if '硕士及以上' in city_edu.index and '本科及以上' in city_edu.index:
                    m = city_edu['硕士及以上']
                    b = city_edu['本科及以上']
                    gap = m - b
                    pct = (gap / b) * 100 if b > 0 else 0
                    knowledge.append({
                        "title": f"{city}市硕士与本科薪资对比",
                        "content": (
                            f"{city}市招聘市场中，硕士平均薪资 {m:.1f}K，"
                            f"本科平均薪资 {b:.1f}K，"
                            f"硕士比本科高 {gap:.1f}K（增幅 {pct:.1f}%）。"
                        )
                    })

    # 5. 工作经验与薪资关系
    # 5. 工作经验与薪资关系
    if work_year_col:
        exp_sal = df.groupby(work_year_col)['salary_avg'].agg(['mean', 'count']).sort_values('mean', ascending=False)
        exp_lines = [f"{idx}: 平均 {row['mean']:.1f}K (共 {row['count']} 条)" for idx, row in exp_sal.iterrows()]
        knowledge.append({
            "title": "工作经验与薪资关系",
            "content": "不同工作经验对应的平均薪资：\n" + "\n".join(exp_lines)
        })

    # 6. 公司规模与薪资
    # 6. 公司规模与薪资
    if company_size_col:
        size_sal = df.groupby(company_size_col)['salary_avg'].agg(['mean', 'count']).sort_values('mean', ascending=False)
        size_lines = [f"{idx}: 平均 {row['mean']:.1f}K (共 {row['count']} 条)" for idx, row in size_sal.iterrows()]
        knowledge.append({
            "title": "公司规模与薪资关系",
            "content": "不同公司规模对应的平均薪资：\n" + "\n".join(size_lines)
        })

    # 7. 典型岗位描述片段（每个keyword取一条代表性描述）
    # 7. 典型岗位描述片段（每个 keyword 取一条代表性描述）
    if position_detail_col:
        for kw in df['keyword'].value_counts().head(20).index:
            sample = df[df['keyword'] == kw].dropna(subset=[position_detail_col]).head(3)
            if not sample.empty:
                details = sample[position_detail_col].tolist()
                clean_details = []
                for d in details:
                    d = str(d).replace('<br>', '').replace('\\n', '').strip()
                    if len(d) > 50:
                        clean_details.append(d[:300])
                if clean_details:
                    knowledge.append({
                        "title": f"{kw} 岗位典型职责与要求",
                        "content": f"{kw}岗位描述示例：" + "\n".join(clean_details)
                    })

    # 8. 通用招聘数据汇总（兜底条目，确保任何问题都有数据支撑）
    # 城市薪资简版
    city_summary = df.groupby('city')['salary_avg'].mean().sort_values(ascending=False).head(10)
    city_summary_str = ", ".join([f"{c}:{s:.1f}K" for c, s in city_summary.items()])
    # 岗位薪资简版
    kw_summary = df.groupby('keyword')['salary_avg'].mean().sort_values(ascending=False).head(10)
    kw_summary_str = ", ".join([f"{k}:{s:.1f}K" for k, s in kw_summary.items()])
    # 学历薪资简版
    edu_summary = df.groupby('edu_norm' if 'edu_norm' in df.columns else 'education')['salary_avg'].mean().sort_values(ascending=False)
    edu_summary_str = ", ".join([f"{e}:{s:.1f}K" for e, s in edu_summary.items()])
    # 经验薪资简版
    # 经验薪资简版
    if work_year_col:
        exp_summary = df.groupby(work_year_col)['salary_avg'].mean().sort_values(ascending=False)
        exp_summary_str = ", ".join([f"{e}:{s:.1f}K" for e, s in exp_summary.items()])
    else:
        exp_summary_str = "数据缺失"

    knowledge.append({
        "title": "通用招聘数据统计汇总",
        "content": (
            f"本数据库共收录 {len(df)} 条招聘数据。"
            f"平均薪资 {avg_s:.1f}K，中位数 {med_s:.1f}K。"
            f"城市平均薪资 Top10：{city_summary_str}。"
            f"热门岗位平均薪资 Top10：{kw_summary_str}。"
            f"学历平均薪资：{edu_summary_str}。"
            f"经验平均薪资：{exp_summary_str}。"
            f"硕士平均薪资 {master_mean:.1f}K（若存在），本科平均薪资 {bachelor_mean:.1f}K（若存在），"
            f"硕士比本科高约 {gap_mean:.1f}K（约 {gap_pct:.1f}%）。"
        )
    })

    # 保存
    with open(RAG_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(knowledge, f, ensure_ascii=False, indent=2)
    logger.info("RAG 知识库已构建，共 %d 条知识条目", len(knowledge))
    return knowledge


# ------------------------------------------------------------------
# 向量化与检索
# ------------------------------------------------------------------

def _call_embedding_api(texts):
    """调用 DashScope Embedding API（复用现有逻辑）"""
    from dashscope import TextEmbedding
    import dashscope
    import os as _os
    dashscope.api_key = _os.getenv("DASHSCOPE_API_KEY", "")
    if not dashscope.api_key:
        raise ValueError("未配置 DASHSCOPE_API_KEY")
    all_embeddings = []
    batch_size = 25
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        response = TextEmbedding.call(
            model='text-embedding-v3',
            input=batch
        )
        if response.status_code == 200:
            for item in response.output['embeddings']:
                all_embeddings.append(item['embedding'])
        else:
            dim = len(all_embeddings[0]) if all_embeddings else 1024
            all_embeddings.extend([np.zeros(dim).tolist()] * len(batch))
    return np.array(all_embeddings, dtype=np.float32)


def cosine_similarity(vec, matrix):
    """计算余弦相似度（支持单向量 vs 矩阵）"""
    norm_vec = np.linalg.norm(vec)
    norm_mat = np.linalg.norm(matrix, axis=1)
    dot = np.dot(matrix, vec)
    return dot / (norm_mat * norm_vec + 1e-10)


class RAGEngine:
    """RAG引擎：负责知识库加载、向量检索、上下文组装"""

    def __init__(self):
        self.knowledge = []
        self.embeddings = None
        self.texts = []
        self._loaded = False
        self._build_if_needed()

    def _build_if_needed(self):
        """若知识库不存在则自动构建"""
        if not os.path.exists(RAG_DATA_PATH):
            logger.info("RAG 知识库不存在，开始自动构建...")
            build_knowledge_base()
        self.load()

    def load(self):
        """加载知识库与向量缓存"""
        with open(RAG_DATA_PATH, 'r', encoding='utf-8') as f:
            self.knowledge = json.load(f)
        self.texts = [item['content'] for item in self.knowledge]
        if os.path.exists(EMBEDDING_CACHE_PATH):
            self.embeddings = np.load(EMBEDDING_CACHE_PATH)
            logger.info("RAG 向量缓存已加载: %s", EMBEDDING_CACHE_PATH)
        else:
            logger.info("RAG 向量缓存不存在，需要重建...")
            self.rebuild_embeddings()
        self._loaded = True

    def rebuild_embeddings(self):
        """重新计算所有知识条目的 Embedding 并缓存"""
        logger.info("开始构建 RAG Embedding，共 %d 条...", len(self.texts))
        self.embeddings = _call_embedding_api(self.texts)
        np.save(EMBEDDING_CACHE_PATH, self.embeddings)
        logger.info("RAG Embedding 构建完成并缓存。")

    def search(self, query, top_k=3):
        """
        检索与 query 最相关的知识片段
        返回: list of dict [{'title', 'content', 'score'}, ...]
        """
        if not self._loaded:
            self.load()
        q_emb = _call_embedding_api([query])[0]
        scores = cosine_similarity(q_emb, self.embeddings)
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            results.append({
                "title": self.knowledge[idx]['title'],
                "content": self.knowledge[idx]['content'],
                "score": float(scores[idx])
            })
        return results


# 单例模式（Streamlit 中复用）
_rag_engine = None

def get_rag_engine():
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine


def rag_chat(user_input, history=None, top_k=5):
    """
    RAG 增强版对话入口：先检索知识库，再将上下文注入 LLM。
    返回: (reply, sources) 其中 sources 为检索到的知识片段列表
    """
    from src.llm_service.chat_api import chat_with_llm
    engine = get_rag_engine()
    sources = engine.search(user_input, top_k=top_k)

    # 组装上下文
    context_blocks = []
    for i, s in enumerate(sources, 1):
        context_blocks.append(f"[知识{i}] {s['title']}\n{s['content']}")
    context_text = "\n\n".join(context_blocks)

    # 构造强约束 RAG 系统 Prompt（禁止推脱）
    rag_system_prompt = (
        "你是「招聘数据智能分析系统」的专属 AI 求职顾问。"
        "以下知识库中已经提供了丰富的招聘统计数据，你的任务是基于这些数据直接回答用户问题。"
        "\n\n【核心指令】"
        "\n1. 必须优先使用知识库中的数据作答，直接引用具体数字和事实。"
        "\n2. 绝对禁止使用以下推脱性表述：'未直接提供'、'知识库中没有'、'没有具体数据'、'未提及'、'根据现有知识库内容'等。"
        "\n3. 如果知识库中有部分相关数据，必须基于已有数据进行分析推断，给出有数据支撑的回答。"
        "\n4. 回答结构：先用数据直接回答问题，再给出分析建议。"
        "\n5. 回答时请务必引用数据出处（如'根据城市薪资排行数据...'、'数据显示...'）。"
        "\n\n===== 知识库参考数据 =====\n"
        f"{context_text}\n"
        "=========================="
    )

    reply = chat_with_llm(user_input, history=history, system_prompt=rag_system_prompt)
    return reply, sources
    return reply, sources
