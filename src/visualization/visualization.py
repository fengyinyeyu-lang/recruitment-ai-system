"""
可视化模块（模块3）
封装全部 5 个核心数据可视化图表的绘制逻辑。
所有函数只返回 matplotlib Figure 对象，不包含任何 Streamlit UI 代码。
"""
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
from wordcloud import WordCloud
import jieba
import os
import pandas as pd
import numpy as np

# ============ 全局样式配置 ============
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.spines.right'] = False

# 统一的商业配色常量
PALETTE_PRIMARY = '#4e73df'
PALETTE_SUCCESS = '#1cc88a'
PALETTE_INFO = '#36b9cc'
PALETTE_WARNING = '#f6c23e'
PALETTE_DANGER = '#e74a3b'
MACAROON_COLORS = [PALETTE_PRIMARY, PALETTE_SUCCESS, PALETTE_INFO, PALETTE_WARNING, PALETTE_DANGER]


import streamlit as st

# @st.cache_resource(show_spinner=False)  # 移除缓存以解决 Matplotlib 渲染线程卡死问题
def plot_salary_distribution(df, salary_col='salary_avg'):
    """
    图表1：全行业薪资分布直方图（含核密度估计）
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    data = df[salary_col].dropna()
    sns.histplot(data, bins=25, kde=True, ax=ax, color=PALETTE_PRIMARY, edgecolor='white', alpha=0.8)
    ax.set_xlabel('平均月薪 (K)', fontsize=12, color='#555')
    ax.set_ylabel('岗位数量', fontsize=12, color='#555')
    ax.set_title('全行业薪资分布', fontsize=14, fontweight='bold', color='#2b3a4a')
    ax.tick_params(colors='#777')
    ax.grid(axis='y', linestyle='--', alpha=0.4, color='#ddd')
    plt.tight_layout()
    return fig


# @st.cache_resource(show_spinner=False)  # 移除缓存以解决 Matplotlib 渲染线程卡死问题
def plot_city_salary(df, city_col='city', salary_col='salary_avg', top_n=10):
    """
    图表2：城市平均薪酬对比条形图
    """
    city_salary = df.groupby(city_col)[salary_col].mean().sort_values(ascending=False).head(top_n)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=city_salary.index, y=city_salary.values, ax=ax,
                hue=city_salary.index, palette='mako', legend=False)
    ax.set_xlabel('城市', fontsize=12, color='#555')
    ax.set_ylabel('平均薪资 (K)', fontsize=12, color='#555')
    ax.set_title('Top城市薪酬对比', fontsize=14, fontweight='bold', color='#2b3a4a')
    plt.xticks(rotation=45, color='#777')
    plt.yticks(color='#777')
    ax.grid(axis='y', linestyle='--', alpha=0.4, color='#ddd')
    plt.tight_layout()
    return fig


# @st.cache_resource(show_spinner=False)  # 移除缓存以解决 Matplotlib 渲染线程卡死问题
def plot_education_pie(df, edu_col='education'):
    """
    图表3：学历要求分布饼图
    """
    fig, ax = plt.subplots(figsize=(8, 8))
    edu_counts = df[edu_col].value_counts()
    colors = MACAROON_COLORS[:len(edu_counts)]
    ax.set_aspect('equal')
    wedges, texts, autotexts = ax.pie(
        edu_counts.values,
        labels=edu_counts.index,
        autopct='%1.1f%%',
        startangle=140,
        colors=colors,
        radius=0.8,
        pctdistance=0.7,
        textprops={'fontsize': 12, 'color': '#333'}
    )
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_weight('bold')
    ax.axis('off')
    ax.set_title('学历准入门槛分布', fontsize=14, fontweight='bold', color='#2b3a4a', pad=20)
    plt.tight_layout()
    return fig


# @st.cache_resource(show_spinner=False)  # 移除缓存以解决 Matplotlib 渲染线程卡死问题
def generate_wordcloud(df, text_col='positionDetail', max_words=150):
    """
    图表4：岗位描述核心技能词云
    """
    # 合并文本列
    text_data = df[text_col].dropna().tolist()
    if 'positionName' in df.columns:
        text_data += df['positionName'].dropna().tolist()
    raw_text = ' '.join(text_data)

    # jieba 分词
    words = jieba.cut(raw_text)
    stopwords = {'的', '了', '在', '是', '有', '和', '不', '人', '都', '要',
                 '也', '就', '到', '说', '会', '你', '我', '他', '她', '这',
                 'br', '熟悉', '使用', '能力', '相关', '以上', '工作', '经验',
                 '优先', '负责', '进行', '具备', '良好', '能够', '项目', '开发',
                 '技术', '公司', '团队', '参与', '了解', '系统'}
    words_filtered = [w for w in words if len(w) > 1 and w not in stopwords]
    words_str = ' '.join(words_filtered)

    font_path = "C:/Windows/Fonts/simhei.ttf" if os.path.exists("C:/Windows/Fonts/simhei.ttf") else None

    wc = WordCloud(
        font_path=font_path,
        background_color='white',
        colormap='GnBu',
        width=800,
        height=400,
        max_words=max_words,
        contour_width=0,
        scale=2
    ).generate(words_str)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    ax.set_title('岗位核心技能画像', fontsize=14, fontweight='bold', color='#2b3a4a', pad=10)
    plt.tight_layout()
    return fig


# @st.cache_resource(show_spinner=False)  # 移除缓存以解决 Matplotlib 渲染线程卡死问题
def plot_experience_salary(df, exp_col='workYear', salary_col='salary_avg'):
    """
    图表5：工作经验与薪资关联箱线图
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # 确定排序顺序
    order = ['应届生', '1年以下', '1-3年', '3-5年', '5-10年', '10年以上', '经验不限']
    # 过滤数据中实际存在的值
    existing_order = [o for o in order if o in df[exp_col].unique()]

    if not existing_order:
        # 如果映射后找不到，就按原始数据画
        existing_order = df[exp_col].value_counts().index.tolist()

    sns.boxplot(x=exp_col, y=salary_col, data=df, order=existing_order, ax=ax,
                hue=df[exp_col] if len(existing_order) > 0 else None,
                palette='mako', legend=False)

    ax.set_xlabel('工作经验', fontsize=12, color='#555')
    ax.set_ylabel('平均薪资 (K)', fontsize=12, color='#555')
    ax.set_title('工作经验与薪资关联分析', fontsize=14, fontweight='bold', color='#2b3a4a')
    ax.tick_params(colors='#777')
    plt.xticks(rotation=30)
    ax.grid(axis='y', linestyle='--', alpha=0.4, color='#ddd')
    plt.tight_layout()
    return fig


# @st.cache_resource(show_spinner=False)  # 移除缓存以解决 Matplotlib 渲染线程卡死问题
def plot_position_demand(count_df, top_n=20):
    """
    附加图表：岗位需求量 Top-N 柱状图（基于 count_positions.csv）
    """
    plot_data = count_df.head(top_n)
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(plot_data['keyword'], plot_data['count'], color=PALETTE_PRIMARY, edgecolor='white', alpha=0.85)
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2., height,
                f'{int(height)}', ha='center', va='bottom', fontsize=8, color='#555')
    ax.set_xlabel('岗位关键字', fontsize=12, color='#555')
    ax.set_ylabel('需求数量', fontsize=12, color='#555')
    ax.set_title(f'Top {top_n} 热门岗位需求分布', fontsize=14, fontweight='bold', color='#2b3a4a')
    plt.xticks(rotation=45, ha='right', color='#777')
    plt.yticks(color='#777')
    ax.grid(axis='y', linestyle='--', alpha=0.4, color='#ddd')
    plt.tight_layout()
    return fig


# @st.cache_resource(show_spinner=False)  # 移除缓存以解决 Matplotlib 渲染线程卡死问题
def plot_horizontal_bar(series, title, xlabel, color=PALETTE_PRIMARY):
    """
    绘制水平条形图，完美解决中文 x 轴标签文字旋转、重叠的反人类问题
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 按照数值大小进行升序排序，使条形图上从上到下由大到小排列
    series_sorted = series.sort_values(ascending=True)
    
    bars = ax.barh(series_sorted.index, series_sorted.values, color=color, edgecolor='white', alpha=0.85)
    
    # 在水平条形图的右侧添加具体数值标签
    for bar in bars:
        width = bar.get_width()
        ax.text(width + (width * 0.005) + 0.1, bar.get_y() + bar.get_height()/2,
                f'{int(width):,}', 
                ha='left', va='center', fontsize=9, color='#4a5568')
                
    ax.set_title(title, fontsize=14, fontweight='bold', color='#2b3a4a', pad=15)
    ax.set_xlabel(xlabel, fontsize=11, color='#4a5568')
    ax.tick_params(colors='#4a5568', labelsize=10)
    ax.grid(axis='x', linestyle='--', alpha=0.4, color='#cbd5e1')
    
    # 移除上方和右方的无用轴线，提升界面清爽感
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    return fig