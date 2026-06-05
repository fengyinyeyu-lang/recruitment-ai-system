"""
大模型服务模块（模块5）
封装通义千问 DashScope API 的调用逻辑。
支持两种模式：
  - 原生模型对话（qwen-turbo）
  - 百炼智能体对话（Application.call）
"""
import os
import dashscope
import logging
from http import HTTPStatus

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


def generate_followup_questions(history):
    """
    根据历史对话内容，调用通义千问大模型动态生成 2 个相关的求职/面试后续追问问题。
    返回包含 2 个字符串的列表。如果失败，则回退到随机推荐词。
    """
    if not history:
        from src.llm_service.prompts import get_random_prompts
        return get_random_prompts(2)

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        from src.llm_service.prompts import get_random_prompts
        return get_random_prompts(2)

    dashscope.api_key = api_key

    # 构建生成追问的系统提示词
    system_prompt = (
        "你是一个求职建议助手的引导模块。请根据给出的历史对话上下文，"
        "生成 2 个用户可能会想继续追问的、短小精炼的后续求职问题。"
        "要求：\n"
        "1. 只输出这两个问题本身，每个问题独占一行，禁止带有任何序号（如 1., 2.）或前缀；\n"
        "2. 问题必须与上下文紧密相关，且属于求职、简历、面试或职业发展范畴；\n"
        "3. 每个问题长度控制在 25 字以内，必须是完整的疑问句。"
    )

    # 提取最后 3 轮对话（即 6 条消息）以保持上下文长度适中
    messages = [{'role': 'system', 'content': system_prompt}]
    for msg in history[-6:]:
        messages.append({'role': msg['role'], 'content': msg['content']})
    messages.append({'role': 'user', 'content': "请根据上述对话历史，直接给出 2 个简短的后续追问问题（每行一个）："})

    try:
        response = dashscope.Generation.call(
            model='qwen-turbo',
            messages=messages,
            result_format='message'
        )
        if response.status_code == 200:
            content = response.output.choices[0].message.content.strip()
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            # 清理可能残留的标记、数字前缀或标点
            import re
            cleaned_lines = []
            for line in lines:
                cleaned = re.sub(r'^(?:\d+[\.、\s]|\-\s|问题[一二三四五\d]+[:：]?\s*)', '', line).strip()
                if cleaned:
                    cleaned_lines.append(cleaned)
            if len(cleaned_lines) >= 2:
                return cleaned_lines[:2]
    except Exception as e:
        logging.error(f"动态追问生成异常: {e}")

    from src.llm_service.prompts import get_random_prompts
    return get_random_prompts(2)


def chat_with_agent(user_input, history=None, session_id=None):
    """
    调用百炼智能体应用进行对话

    参数:
        user_input: 用户当前输入
        history: 历史对话列表（智能体模式下由 session_id 管理上下文，此参数备用）
        session_id: 会话ID，传入后智能体可自动维护多轮上下文

    返回:
        (reply, session_id) 元组
    """
    from dashscope import Application

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return "⚠️ 错误：未检测到 DASHSCOPE_API_KEY 环境变量，请在系统环境变量中配置后重启应用。", None

    app_id = os.getenv("DASHSCOPE_APP_ID")
    if not app_id:
        return "⚠️ 错误：未检测到 DASHSCOPE_APP_ID 环境变量，请在 .env 中配置智能体应用 ID。", None

    try:
        kwargs = dict(
            api_key=api_key,
            app_id=app_id,
            prompt=user_input,
        )
        # 传入 session_id 实现多轮对话
        if session_id:
            kwargs["session_id"] = session_id

        response = Application.call(**kwargs)

        if response.status_code == HTTPStatus.OK:
            reply = response.output.text
            new_session_id = response.output.session_id if hasattr(response.output, 'session_id') else None
            return reply, new_session_id
        else:
            return f"⚠️ 智能体调用失败 [{response.status_code}]: {response.message}", None
    except Exception as e:
        logging.error(f"智能体请求异常: {e}")
        return f"⚠️ 请求异常: {str(e)}", None


def chat_with_agent_stream(user_input, session_id=None):
    """
    流式调用百炼智能体应用，逐段返回文本。

    参数:
        user_input: 用户当前输入
        session_id: 会话ID

    生成:
        dict: {"type": "text", "content": "..."} 或 {"type": "done", "session_id": "..."}
    """
    import time
    from dashscope import Application

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        yield {"type": "text", "content": "⚠️ 错误：未检测到 DASHSCOPE_API_KEY 环境变量。"}
        yield {"type": "done", "session_id": None}
        return

    app_id = os.getenv("DASHSCOPE_APP_ID")
    if not app_id:
        yield {"type": "text", "content": "⚠️ 错误：未检测到 DASHSCOPE_APP_ID 环境变量。"}
        yield {"type": "done", "session_id": None}
        return

    try:
        kwargs = dict(
            api_key=api_key,
            app_id=app_id,
            prompt=user_input,
            stream=True,
            incremental_output=True,
        )
        if session_id:
            kwargs["session_id"] = session_id

        start_time = time.time()
        responses = Application.call(**kwargs)
        new_session_id = None
        first_token = True

        for response in responses:
            if response.status_code == HTTPStatus.OK:
                text = response.output.text if hasattr(response.output, 'text') else ""
                if text:
                    if first_token:
                        latency = (time.time() - start_time) * 1000
                        logging.info(f"[Agent] 首 Token 延迟: {latency:.0f}ms")
                        first_token = False
                    yield {"type": "text", "content": text}
                if hasattr(response.output, 'session_id') and response.output.session_id:
                    new_session_id = response.output.session_id
            else:
                yield {"type": "text", "content": f"⚠️ 智能体调用失败 [{response.status_code}]: {response.message}"}
                break

        total_time = (time.time() - start_time) * 1000
        logging.info(f"[Agent] 总耗时: {total_time:.0f}ms")
        yield {"type": "done", "session_id": new_session_id}

    except Exception as e:
        logging.error(f"智能体流式请求异常: {e}")
        yield {"type": "text", "content": f"⚠️ 请求异常: {str(e)}"}
        yield {"type": "done", "session_id": None}

