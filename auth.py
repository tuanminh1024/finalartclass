import os
import hmac
import streamlit as st


def get_allowed_users():
    """
    Đọc danh sách user từ biến môi trường:
    APP_USERS=user1:pass1,user2:pass2
    """
    raw = os.environ.get("APP_USERS", "").strip()
    users = {}

    if not raw:
        return users

    pairs = [x.strip() for x in raw.split(",") if x.strip()]
    for pair in pairs:
        if ":" in pair:
            username, password = pair.split(":", 1)
            users[username.strip()] = password.strip()

    return users


def check_login(username: str, password: str) -> bool:
    users = get_allowed_users()
    if username not in users:
        return False
    return hmac.compare_digest(users[username], password)


def init_auth_state():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = ""


def login_form():
    st.title("🔐 Đăng nhập hệ thống")
    st.caption("Vui lòng nhập tài khoản và mật khẩu để sử dụng ứng dụng")

    with st.form("login_form"):
        username = st.text_input("Tài khoản")
        password = st.text_input("Mật khẩu", type="password")
        submitted = st.form_submit_button("Đăng nhập", use_container_width=True)

    if submitted:
        if check_login(username.strip(), password):
            st.session_state["authenticated"] = True
            st.session_state["username"] = username.strip()
            st.success("Đăng nhập thành công")
            st.rerun()
        else:
            st.error("Sai tài khoản hoặc mật khẩu")


def require_login():
    init_auth_state()

    if not st.session_state["authenticated"]:
        users = get_allowed_users()
        if not users:
            st.error("Chưa cấu hình APP_USERS trong biến môi trường.")
            st.stop()

        login_form()
        st.stop()


def logout_button():
    if st.sidebar.button("Đăng xuất", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["username"] = ""
        st.rerun()
