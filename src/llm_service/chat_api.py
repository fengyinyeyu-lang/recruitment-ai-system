"""
大模型服务模块（模块5）
封装通义千问 DashScope API 的调用逻辑。
"""
import os
import dashscope
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 默认系统提示词
DEFAULT_SYSTEM_PROMPT = (
    "你是「招聘数据智能分析系统」的专属 AI 求职顾问。"
    "你精通互联网招聘市场趋势、简历优化技巧和面试准备策略。"
    "请根据用户的问题，给出专业、结构化的回答。"
    "如果用户问的是与招聘/求职无关的话题，也要友好地回应，并尝试引导回求职主题。"
)


def chat_with_llm(user_input, history=None, system_prompt=None):
    """
    调用通义千问大模型进行对话

    参数:
        user_input: 用户当前输入
        history: 历史对话列表 [{'role':'user','content':'...'}, ...]
        system_prompt: 系统提示词（可选覆盖）

    返回:
        AI 回复文本
    """
    if history is None:
        history = []
    if system_prompt is None:
        system_prompt = DEFAULT_SYSTEM_PROMPT

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return "⚠️ 错误：未检测到 DASHSCOPE_API_KEY 环境变量，请在系统环境变量中配置后重启应用。"

    dashscope.api_key = api_key

    # 构建消息列表
    messages = [{'role': 'system', 'content': system_prompt}]
    for msg in history:
        if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
            messages.append({'role': msg['role'], 'content': msg['content']})
    messages.append({'role': 'user', 'content': user_input})

    try:
        response = dashscope.Generation.call(
            model='qwen-turbo',
            messages=messages,
            result_format='message'
        )
        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            return f"⚠️ API 调用失败 [{response.code}]: {response.message}"
    except Exception as e:
        logging.error(f"大模型请求异常: {e}")
        return f"⚠️ 请求异常: {str(e)}"
