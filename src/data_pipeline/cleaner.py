"""
数据清洗模块（模块2）
负责从原始CSV中加载数据，进行薪资解析、经验/学历标准化、缺失值/重复值处理，
并输出清洗后的高质量数据集。
"""
import pandas as pd
import numpy as np
import re
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 项目根目录（相对于本文件向上两级）
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


class DataCleaner:
    """招聘数据清洗器"""

    def __init__(self, data_path=None):
        if data_path is None:
            data_path = os.path.join(PROJECT_ROOT, 'data', 'raw', '拉勾网2023招聘数据.csv')

        if not os.path.exists(data_path):
            raise FileNotFoundError(f"原始数据文件不存在: {data_path}")

        self.df = pd.read_csv(data_path, encoding='utf-8')
        logging.info(f"成功加载原始数据，共 {len(self.df)} 条记录，{len(self.df.columns)} 个字段。")

        # 预处理：统一关键字格式
        if 'keyword' in self.df.columns:
            self.df['keyword'] = self.df['keyword'].astype(str).str.strip().str.upper()
            self.df['keyword'] = self.df['keyword'].replace('PHP工程师', 'PHP')

    def clean_salary(self):
        """
        清洗薪资数据：
        将 '15k-30k' 格式解析为 salary_low, salary_high, salary_avg 三列（单位：K）
        """
        def parse_salary(salary_str):
            if pd.isna(salary_str):
                return np.nan, np.nan, np.nan
            s = str(salary_str).strip().lower()
            # 匹配 "15k-30k" 或 "15K-30K" 格式
            match = re.match(r'(\d+)k?\s*-\s*(\d+)k?', s)
            if match:
                low = float(match.group(1))
                high = float(match.group(2))
                return low, high, (low + high) / 2
            return np.nan, np.nan, np.nan

        parsed = self.df['salary'].apply(parse_salary)
        self.df['salary_low'] = parsed.apply(lambda x: x[0])
        self.df['salary_high'] = parsed.apply(lambda x: x[1])
        self.df['salary_avg'] = parsed.apply(lambda x: x[2])
        logging.info("成功清洗薪资数据。有效解析率: %.1f%%",
                      self.df['salary_avg'].notna().mean() * 100)

    def clean_work_year_and_edu(self):
        """标准化工作经验和学历要求字段"""
        # 工作经验标准化映射
        work_year_map = {
            '应届毕业生': '应届生',
            '不限': '经验不限',
            '1年以下': '1年以下',
            '1-3年': '1-3年',
            '3-5年': '3-5年',
            '5-10年': '5-10年',
            '10年以上': '10年以上',
        }
        if 'workYear' in self.df.columns:
            self.df['workYear'] = self.df['workYear'].astype(str).str.strip()
            self.df['workYear'] = self.df['workYear'].map(
                lambda x: work_year_map.get(x, x)
            )

        # 学历标准化
        edu_map = {
            '不限': '不限', '大专': '大专', '本科': '本科',
            '硕士': '硕士', '博士': '博士',
        }
        if 'education' in self.df.columns:
            self.df['education'] = self.df['education'].astype(str).str.strip()
            self.df['education'] = self.df['education'].map(
                lambda x: edu_map.get(x, x)
            )
        logging.info("成功标准化工作经验和学历要求。")

    def handle_missing_and_duplicates(self):
        """处理缺失值和重复值"""
        original_len = len(self.df)

        # 去除完全重复的行
        self.df.drop_duplicates(inplace=True)
        dup_removed = original_len - len(self.df)

        # 关键字段缺失值处理
        critical_cols = ['positionName', 'salary', 'city']
        self.df.dropna(subset=critical_cols, inplace=True)

        # 非关键字段填充默认值
        fill_defaults = {
            'companySize': '未知',
            'industryField': '未知',
            'financeStage': '未知',
            'education': '不限',
            'workYear': '经验不限',
            'positionDetail': '',
            'positionAdvantage': '',
        }
        for col, default in fill_defaults.items():
            if col in self.df.columns:
                self.df[col] = self.df[col].fillna(default)

        # 清理薪资解析失败的行
        if 'salary_avg' in self.df.columns:
            self.df.dropna(subset=['salary_avg'], inplace=True)

        final_len = len(self.df)
        logging.info(
            "去重 %d 条，缺失值处理后剩余 %d 条（共移除 %d 条）。",
            dup_removed, final_len, original_len - final_len
        )

    def count_positions(self, to_csv_path=None, min_count=0):
        """统计各岗位关键字的需求数量"""
        if to_csv_path is None:
            to_csv_path = os.path.join(PROJECT_ROOT, 'data', 'processed', 'count_positions.csv')

        positions = self.df['keyword'].value_counts()
        positions = positions[positions >= min_count]
        positions = positions.reset_index()
        positions.columns = ['keyword', 'count']
        positions.to_csv(to_csv_path, index=False, encoding='utf-8-sig')
        logging.info(f"岗位统计完成，共 {len(positions)} 个类别，已保存至 {to_csv_path}")

    def save_processed(self, output_path=None):
        """保存清洗后的完整数据集"""
        if output_path is None:
            output_path = os.path.join(PROJECT_ROOT, 'data', 'processed', 'cleaned_jobs.csv')

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self.df.to_csv(output_path, index=False, encoding='utf-8-sig')
        logging.info(f"清洗后数据已保存至 {output_path}，共 {len(self.df)} 条。")

    def run_full_pipeline(self):
        """执行完整的数据清洗流水线"""
        self.clean_salary()
        self.clean_work_year_and_edu()
        self.handle_missing_and_duplicates()
        self.count_positions()
        self.save_processed()
        return self.df


import streamlit as st

@st.cache_data(show_spinner=False)
def load_processed_data(file_path=None):
    """加载已清洗的数据（供前端页面调用，并使用 Streamlit 缓存加速）"""
    if file_path is None:
        file_path = os.path.join(PROJECT_ROOT, 'data', 'processed', 'cleaned_jobs.csv')
    if not os.path.exists(file_path):
        return None
    try:
        return pd.read_csv(file_path, encoding='utf-8-sig')
    except Exception:
        return pd.read_csv(file_path, encoding='utf-8')


@st.cache_data(show_spinner=False)
def load_count_positions(file_path=None):
    """加载岗位统计数据（供前端页面调用，并使用 Streamlit 缓存加速）"""
    if file_path is None:
        file_path = os.path.join(PROJECT_ROOT, 'data', 'processed', 'count_positions.csv')
    if not os.path.exists(file_path):
        return None
    return pd.read_csv(file_path, encoding='utf-8-sig')


if __name__ == "__main__":
    cleaner = DataCleaner()
    cleaner.run_full_pipeline()