"""
提示词工程模板（Prompt Engineering）
为 AI 智能客服提供预置的高质量提示词模板。
"""
import random

# 猜你想问的快捷提示词池
QUICK_PROMPTS = [
    "怎么写一份吸引HR的Java后端简历？",
    "今年人工智能行业的发展趋势和平均薪资如何？",
    "面试大厂测试开发工程师需要准备哪些技术栈？",
    "帮我模拟一段数据分析师的专业面试自我介绍。",
    "转行做前端开发，零基础需要学习哪些知识？",
    "Python 开发工程师在一线城市的薪资水平怎样？",
    "如何在面试中回答「你的职业规划是什么」？",
    "机器学习工程师和算法工程师有什么区别？",
]


def get_random_prompts(n=2):
    """从提示词池中随机抽取 n 条不重复的提示词"""
    if n > len(QUICK_PROMPTS):
        n = len(QUICK_PROMPTS)
    return random.sample(QUICK_PROMPTS, n)
