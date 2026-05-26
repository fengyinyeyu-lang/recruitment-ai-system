"""
NLP 文本预处理模块
负责分词、去停用词、TF-IDF 特征提取、以及基于大模型 Embedding API 的文本向量化操作。
"""
import jieba
import re
import os
import time
import logging
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# 默认停用词表（常见高频无意义词）
DEFAULT_STOPWORDS = {
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
    '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着',
    '没有', '看', '好', '自己', '这', '他', '她', '吗', '知道', '啊',
    '熟悉', '能够', '具有', '相关', '以上', '经验', '优先', '以及',
    '工作', '负责', '能力', '进行', '公司', '岗位', '职位', '描述',
    '要求', 'br', '具备', '良好', '技术', '使用', '开发', '项目',
    # 方案A额外新增的招聘套话与英文数字噪音
    '具体', '参与', '职责', '任职', '业务', '了解', '掌握', '优秀', 
    '实现', '包括', '方向', '支持', '研究', '解决', 'and', 'or', 'the', 
    'in', 'of', 'to', 'with', 'for', 'on', 'at', 'is', 'are', 'be',
    '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
    # 进一步屏蔽噪音
    '推荐', '需要', '我们', '提供', '各种', '不同', '优先考虑', '等等',
    '熟练', '熟练掌握', '可以', '作为', '或者', '基础', '一定', '完成',
    '协助', '深入', '日常', '根据', '其它', '其他', '以及', '具有', '要求',
    '岗位职责', '任职要求', '工作职责', '岗位要求', '本科及以上学历', 
    '以上学历', '任职资格', '工作内容',
    # 方案1新增的高频非技术噪音词（招聘套话、福利、软实力、日常管理等通用词）
    '限于', '细致', '思维', '带薪', '福利', '双休', '待遇', '五险一金', '年终奖',
    '定期体检', '员工旅游', '晋升', '空间', '弹性', '氛围', '团队', '活力', '激情',
    '办公', '环境', '扁平', '管理', '培训', '社保', '公积金', '绩效', '奖金', '体检',
    '旅游', '不限', '日常', '沟通', '协作', '精神', '执行力', '抗压', '学习', '主动',
    '责任心', '乐观', '开朗', '诚实', '守信', '处理', '独立', '快速', '热爱', '兴趣',
    '专业', '企业', '平台', '产品', '系统', '需求', '研发', '工程', '工程师', '代码',
    '质量', '性能', '优化', '提升', '维护', '支撑', '保障', '运行', '线上', '故障',
    '问题', '协同', '配合', '大专', '本科', '硕士', '研究生', '博士', '及以上', '学历',
    '计算机', '软件', '难题', '技术难题', '挑战', '规范', '标准', '编写', '设计',
    '合理', '稳定', '机制', '持续', '保证', '提供', '岗位要求', '任职条件', '基本条件',
    '职位描述', '职位要求', '主要职责', '配合工作', '积极主动', '学习能力', '抗压能力',
    '沟通能力', '团队合作', '团队精神', '工作经验', '相关专业', '薪资', '五险', '一金',
    '带薪年假', '节日礼品', '下午茶', '详谈', '面议', '面谈', '体系统', 'middot'
}

# Embedding 缓存目录
EMBEDDING_CACHE_DIR = os.path.join(PROJECT_ROOT, 'data', 'text_features')

# 采样上限
MAX_SAMPLE_SIZE = 6000
# 每批 API 请求条数上限
API_BATCH_SIZE = 10
# 批次间休眠秒数
BATCH_SLEEP_SECONDS = 0.5


def clean_text(text):
    """
    清洗文本：
    1. 去 HTML 标签
    2. 去 HTML 实体（如 &middot;, &quot; 等所有以 & 开头 ; 结尾的符号）
    3. 只保留中英文（保留英文技术词，过滤数字/标点）
    """
    if pd.isna(text):
        return ""
    text = str(text)
    # 去 HTML 标签
    text = re.sub(r'<[^>]+>', ' ', text)
    # 彻底去除 HTML 实体字符，避免 markdown/middot 变成字母残留
    text = re.sub(r'&[a-zA-Z0-9#]+;', ' ', text)
    # 强制清除不完整的 HTML nbsp 空格残留
    text = text.replace('&nbsp;', ' ').replace('nbsp', ' ')
    # 只保留中文和英文字母
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()

# 为了向下兼容，保留 clean_html_tags 别名
clean_html_tags = clean_text


def tokenize(text, stopwords=None):
    """使用 jieba 分词并过滤停用词"""
    if stopwords is None:
        stopwords = DEFAULT_STOPWORDS
    words = jieba.cut(str(text))
    return " ".join([w for w in words if len(w) > 1 and w not in stopwords])


def build_tfidf_matrix(texts, max_features=1000):
    """
    构建 TF-IDF 特征矩阵
    返回: (稀疏矩阵, TfidfVectorizer 实例)
    """
    vectorizer = TfidfVectorizer(max_features=max_features)
    X = vectorizer.fit_transform(texts)
    return X, vectorizer


def preprocess_text_column(df, text_col='positionDetail'):
    """
    对 DataFrame 中指定的文本列进行完整预处理：
    清洗 HTML -> 分词 -> 返回处理后的 Series
    """
    cleaned = df[text_col].apply(clean_text)
    tokenized = cleaned.apply(tokenize)
    return tokenized


def _call_embedding_api(texts, progress_callback=None):
    """
    调用阿里云 DashScope TextEmbedding API，将文本列表转换为稠密向量。
    内部按 API_BATCH_SIZE 分批请求，批次间 sleep(BATCH_SLEEP_SECONDS)。

    参数:
        texts: 文本列表（已预处理、已截断）
        progress_callback: 进度回调函数，签名 func(done: int, total: int)

    返回:
        numpy 数组，形状为 (len(texts), embedding_dim)
    """
    import dashscope
    from dashscope import TextEmbedding

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError(
            "未检测到 DASHSCOPE_API_KEY 环境变量。"
            "请在系统环境变量中配置阿里云百炼 API Key 后重启应用。"
        )
    dashscope.api_key = api_key

    all_embeddings = []
    total = len(texts)

    for i in range(0, total, API_BATCH_SIZE):
        batch = texts[i:i + API_BATCH_SIZE]
        # DashScope 不接受空字符串，用占位符替代
        batch = [t if t and t.strip() else "空" for t in batch]

        try:
            response = TextEmbedding.call(
                model='text-embedding-v3',
                input=batch,
            )
            if response.status_code == 200:
                embeddings = [item['embedding'] for item in response.output['embeddings']]
                all_embeddings.extend(embeddings)
            else:
                logging.error(
                    "Embedding API 调用失败 [%s]: %s", response.code, response.message
                )
                dim = len(all_embeddings[0]) if all_embeddings else 1024
                all_embeddings.extend([np.zeros(dim).tolist()] * len(batch))
        except Exception as e:
            logging.error("Embedding API 请求异常: %s", e)
            dim = len(all_embeddings[0]) if all_embeddings else 1024
            all_embeddings.extend([np.zeros(dim).tolist()] * len(batch))

        done = min(i + API_BATCH_SIZE, total)
        logging.info("Embedding 进度: %d / %d", done, total)
        
        # 触发回调以更新 UI
        if progress_callback is not None:
            progress_callback(done, total)

        # 批次间休眠，避免触发 API 限流
        if done < total:
            time.sleep(BATCH_SLEEP_SECONDS)

    return np.array(all_embeddings, dtype=np.float32)


def get_sampled_df(df, actual_size=6000):
    """按照每类最多500条的逻辑进行均匀抽样，防止个别庞大类别主导聚类结果"""
    if 'keyword' in df.columns:
        # 按照 keyword 进行分层抽样，每类最多500条
        sampled_df = df.groupby('keyword', group_keys=False).apply(lambda x: x.sample(min(len(x), 500), random_state=42))
        # 如果总量还是超过上限，再进行随机截断
        if len(sampled_df) > actual_size:
            sampled_df = sampled_df.sample(actual_size, random_state=42)
        return sampled_df
    else:
        if len(df) > actual_size:
            return df.sample(actual_size, random_state=42)
        return df

def build_embedding_matrix(df, text_col='positionDetail', cache_name='embeddings',
                           sample_size=None, progress_callback=None):
    """
    对 DataFrame 的文本列进行 Embedding 向量化。
    严格缓存优先：缓存存在则直接加载返回，不存在才调用 API 并立即保存。

    参数:
        df: 清洗后的 DataFrame
        text_col: 文本特征列名
        cache_name: 缓存文件名前缀
        sample_size: 采样数（None 则使用 MAX_SAMPLE_SIZE 上限）

    返回:
        embedding_matrix: np.ndarray, 形状 (n_samples, embedding_dim)
    """
    os.makedirs(EMBEDDING_CACHE_DIR, exist_ok=True)

    # 确定实际采样数（上限 MAX_SAMPLE_SIZE）
    if sample_size is None:
        actual_size = min(len(df), MAX_SAMPLE_SIZE)
    else:
        actual_size = min(sample_size, MAX_SAMPLE_SIZE, len(df))

    cache_path = os.path.join(EMBEDDING_CACHE_DIR, f"{cache_name}_{actual_size}.npy")

    # ===== 第一步：检查缓存 =====
    if os.path.exists(cache_path):
        logging.info("命中缓存，跳过 API 调用: %s", cache_path)
        return np.load(cache_path)

    # ===== 第二步：采样 + 调用 API =====
    logging.info("缓存未命中，开始进行均匀分层采样（每类最大500条），目标总数约 %d 条，并调用 API...", actual_size)
    sampled_df = get_sampled_df(df, actual_size)

    # 文本预处理：清洗 HTML + 截断
    texts = sampled_df[text_col].fillna('').apply(clean_text).tolist()
    texts = [t[:2000] if len(t) > 2000 else t for t in texts]

    embedding_matrix = _call_embedding_api(texts, progress_callback=progress_callback)

    # ===== 第三步：立即保存缓存 =====
    np.save(cache_path, embedding_matrix)
    logging.info("Embedding 缓存已保存: %s (形状: %s)", cache_path, embedding_matrix.shape)

    return embedding_matrix
