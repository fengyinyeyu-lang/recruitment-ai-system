"""
认证组件
用户登录/注册的交互逻辑。
"""
import json
import os
import streamlit as st

# 用户数据文件路径（存放在项目 data 目录下）
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
USERS_FILE = os.path.join(PROJECT_ROOT, 'data', 'users.json')


def _load_users():
    """加载用户数据"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def _save_users(users):
    """保存用户数据"""
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)


def login(username, password):
    """验证用户登录"""
    users = _load_users()
    if username in users and users[username] == password:
        st.session_state['logged_in'] = True
        st.session_state['username'] = username
        return True
    return False


def register(username, password):
    """注册新用户"""
    if not username or len(username) < 3:
        return False, "用户名长度不能少于3个字符"
    if not password or len(password) < 6:
        return False, "密码长度不能少于6个字符"

    users = _load_users()
    if username in users:
        return False, "用户名已存在"

    users[username] = password
    _save_users(users)
    
    # 注册成功后直接写入登录态，实现自动登录
    st.session_state['logged_in'] = True
    st.session_state['username'] = username
    return True, "注册成功，正在为您自动登录并进入系统..."


def check_login():
    """检查是否已登录，未登录则展示登录界面并阻止后续渲染"""
    if not st.session_state.get('logged_in', False):
        _render_login_page()
        st.stop()


def _render_login_page():
    """渲染登录/注册页面"""
    # 再次强力确保登录页不渲染侧边栏结构
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none; }
        [data-testid="stSidebarCollapsedControl"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.write("<br><br><br>", unsafe_allow_html=True)
        st.title("💼 招聘智能系统")
        st.markdown(
            "<p style='color:#6c757d; font-size:1.1rem;'>企业级大数据洞察与智能助手</p>",
            unsafe_allow_html=True
        )
        st.write("---")

        choice = st.radio("请选择操作", ["登录", "注册"], horizontal=True, key="auth_choice_radio")
        username = st.text_input("👤 用户名", key="auth_username_input")
        password = st.text_input("🔒 密码", type="password", key="auth_password_input")
        st.write("<br>", unsafe_allow_html=True)

        if choice == "登录":
            if st.button("🚀 登 录 系 统", use_container_width=True, type="primary", key="auth_login_btn"):
                if login(username, password):
                    st.success("登录成功，正在进入系统...")
                    st.rerun()
                else:
                    st.error("用户名或密码错误！")
        else:
            if st.button("📝 注 册 账 号", use_container_width=True, type="primary", key="auth_register_btn"):
                success, msg = register(username, password)
                if success:
                    st.success(msg)
                    import time
                    time.sleep(1)  # 稍微停留一秒展示成功信息，提升体验
                    st.rerun()
                else:
                    st.error(msg)
