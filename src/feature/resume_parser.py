"""
PDF 简历解析与岗位匹配模块（加分项 5）
支持上传 PDF，提取学历、经验、技能关键词，并从岗位库中推荐匹配度最高的工作。
"""
import os
import re
import logging
import pdfplumber
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 技能词库（可扩展）
TECH_SKILLS = [
    'Python', 'Java', 'C++', 'C', 'Go', 'Golang', 'Rust', 'PHP', 'JavaScript', 'JS', 'TypeScript', 'TS',
    'Vue', 'React', 'Angular', 'Node.js', 'HTML', 'CSS',
    'MySQL', 'PostgreSQL', 'Redis', 'MongoDB', 'Oracle', 'SQLite',
    'Spring', 'Django', 'Flask', 'FastAPI', 'TensorFlow', 'PyTorch', 'Keras',
    'Hadoop', 'Spark', 'Flink', 'Kafka', 'Docker', 'Kubernetes', 'K8s', 'Linux', 'Git',
    'NLP', 'CV', 'LLM', 'Transformer', 'Machine Learning', 'ML', 'Deep Learning', 'DL'
]

# 学历映射表
EDUCATION_MAP = {
    '博士': 4, '博士后': 5, '硕士': 3, '研究生': 3, '本科': 2, '学士': 2,
    '大专': 1, '专科': 1, '高中': 0, '中专': 0, '不限': 0
}


def extract_text_from_pdf(uploaded_file):
    """从 PDF 文件流中提取文本"""
    try:
        if hasattr(uploaded_file, 'read'):
            with pdfplumber.open(uploaded_file) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
    except Exception as e:
        logging.error(f"PDF 解析失败: {e}")
        return ""


def parse_resume_info(text):
    """从纯文本中解析简历关键信息"""
    if not text:
        return {"education": "", "experience": 0, "skills": [], "raw": ""}

    info = {
        "education": "",
        "experience": 0,
        "skills": [],
        "raw": text
    }

    # 1. 提取学历 (Regex 查找常见学历词汇)
    edu_pattern = r"(?:学历|教育|学位)[:：\s]*(本科|硕士|研究生|博士|大专|专科|高中|中专|不限)"
    edu_match = re.search(edu_pattern, text, re.IGNORECASE)
    if edu_match:
        info["education"] = edu_match.group(1)
    else:
        # 兜底：如果没找到明确格式，直接扫描文本中是否包含这些词
        for edu in ['本科', '硕士', '研究生', '博士', '大专']:
            if edu in text:
                info["education"] = edu
                break

    # 2. 提取工作年限
    exp_pattern = r"(\d+)[年yY]"
    exp_match = re.search(exp_pattern, text)
    if exp_match:
        info["experience"] = int(exp_match.group(1))

    # 3. 提取技能 (词库匹配)
    found_skills = []
    text_lower = text.lower()
    for skill in TECH_SKILLS:
        if skill.lower() in text_lower:
            found_skills.append(skill)
    info["skills"] = found_skills

    return info


def recommend_jobs(resume_info, df_jobs, top_n=5):
    """
    基于简历信息与岗位库进行匹配打分，返回 Top N 推荐列表。
    打分逻辑：
    - 基础分：技能重合度 (每匹配一个技能 +10 分)
    - 学历加分：学历符合要求 +20 分，略低 +10 分
    - 经验加分：经验符合 +15 分
    """
    if df_jobs is None or df_jobs.empty or not resume_info.get("skills"):
        return pd.DataFrame()

    resume_skills = set(resume_info.get("skills", []))
    resume_edu_str = resume_info.get("education", "")
    resume_edu_val = EDUCATION_MAP.get(resume_edu_str, 0)
    resume_exp = resume_info.get("experience", 0)

    scores = []

    for idx, row in df_jobs.iterrows():
        score = 0
        job_skills_str = str(row.get('positionDetail', '')) + " " + str(row.get('keyword', ''))

        # 1. 技能匹配得分 (最核心指标)
        job_skills_match = []
        for s in resume_skills:
            if s.lower() in job_skills_str.lower():
                job_skills_match.append(s)
        
        skill_score = len(job_skills_match) * 10
        score += skill_score

        # 2. 学历要求匹配 (仅当简历有学历信息时)
        if resume_edu_str:
            job_edu = str(row.get('education', '不限'))
            job_edu_val = EDUCATION_MAP.get(job_edu, 0)
            if resume_edu_val >= job_edu_val:
                score += 20
            else:
                # 经验可以弥补学历，但如果差太多则减分
                if resume_exp >= job_edu_val:
                    score += 5
                else:
                    score -= 10

        # 3. 经验匹配
        job_exp_str = str(row.get('workYear', ''))
        # 简单逻辑：如果要求 "经验不限" 或者 "不限"，直接加分
        if '不限' in job_exp_str:
            score += 10
        else:
            # 尝试提取数字（如 3-5年）
            exp_match = re.search(r'(\d+)', job_exp_str)
            if exp_match:
                req_exp = int(exp_match.group(1))
                if resume_exp >= req_exp:
                    score += 15
                elif resume_exp >= req_exp - 1:
                    score += 5

        scores.append((idx, score, job_skills_match))

    # 构建结果 DataFrame
    res_df = df_jobs.copy()
    res_df['_match_score'] = [s[1] for s in scores]
    res_df['_matched_skills'] = [s[2] for s in scores]
    
    # 过滤掉得分低于阈值（例如 10 分）的岗位
    res_df = res_df[res_df['_match_score'] >= 10]
    
    # 排序
    res_df = res_df.sort_values(by='_match_score', ascending=False)
    
    return res_df.head(top_n)
