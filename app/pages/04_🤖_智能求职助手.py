"""
页面4：🤖 智能求职助手
基于通义千问大模型的定制化求职建议与交互问答。
"""
import streamlit as st
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.components.auth import check_login
check_login()

from src.llm_service.chat_api import chat_with_llm
from src.llm_service.prompts import get_random_prompts

st.header("🤖 求职专属大模型 AI 顾问")
st.markdown(
    "<p style='color:#6c757d;'>基于通义千问强大的语义理解，为您提供简历修改、岗位选择、面试准备等定制化求职建议。</p>",
    unsafe_allow_html=True
)
st.write("---")

# ========== 初始化会话状态 ==========
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'ai_quick_prompts' not in st.session_state:
    st.session_state['ai_quick_prompts'] = get_random_prompts(2)

# ========== 渲染聊天记录 ==========
for msg in st.session_state['chat_history']:
    avatar = "🧑‍💻" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ========== 猜你想问快捷胶囊区 ==========
prompt = None

st.markdown(
    "<p style='color:#6c757d; font-size: 0.9em; margin-bottom: 2px;'>💡 猜你想问：</p>",
    unsafe_allow_html=True
)
p1, p2 = st.session_state['ai_quick_prompts']

# 使用动态列宽靠左对齐
c1, c2, _ = st.columns([len(p1) + 5, len(p2) + 5, 40])
with c1:
    if st.button(f"💬 {p1}", type="secondary", use_container_width=False):
        prompt = p1
with c2:
    if st.button(f"💬 {p2}", type="secondary", use_container_width=False):
        prompt = p2

# ========== 底部原生聊天输入框 ==========
if chat_val := st.chat_input("向AI智能顾问提问您的职场疑惑..."):
    prompt = chat_val

# ========== 统一处理提问和AI响应 ==========
if prompt:
    st.session_state['chat_history'].append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("AI 顾问正在思考中..."):
            response = chat_with_llm(prompt, st.session_state['chat_history'][:-1])
            st.markdown(response)
            st.session_state['chat_history'].append({"role": "assistant", "content": response})
