import streamlit as st
from supabase import create_client

# --- 1. การตั้งค่าและการเชื่อมต่อ ---
st.set_page_config(page_title="ระบบมินิเกมจราจร", page_icon="🚦", layout="centered")

@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- 2. ฟังก์ชันระบบ ---

def get_user_role(user_id):
    """ตรวจสอบสิทธิ์จากฐานข้อมูล"""
    try:
        response = supabase.table("profiles").select("role").eq("id", user_id).single().execute()
        return response.data["role"] if response.data else "player"
    except:
        return "player"

def sign_in(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.user:
            st.session_state.user = res.user
            st.session_state.role = get_user_role(res.user.id)
            st.success("เข้าสู่ระบบสำเร็จ!")
            st.rerun()
    except Exception as e:
        st.error("อีเมลหรือรหัสผ่านไม่ถูกต้อง")

def sign_up(email, password, full_name, student_id):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            # กำหนด role เป็น 'player' เสมอสำหรับการสมัครผ่านหน้าเว็บ
            data = {
                "id": res.user.id,
                "full_name": full_name,
                "student_id": student_id,
                "role": "player" 
            }
            supabase.table("profiles").insert(data).execute()
            st.success("สมัครสมาชิกสำเร็จ! กรุณาเข้าสู่ระบบ")
    except Exception as e:
        st.error(f"สมัครสมาชิกล้มเหลว: {e}")

# --- 3. ส่วนหน้าจอแสดงผล ---

if 'user' not in st.session_state:
    st.title("🚦 ระบบมินิเกมจราจร")
    tab_login, tab_signup = st.tabs(["🔐 เข้าสู่ระบบ", "📝 สมัครผู้เล่นใหม่"])

    with tab_login:
        email = st.text_input("อีเมล", key="login_email")
        password = st.text_input("รหัสผ่าน", type="password", key="login_pass")
        if st.button("เข้าสู่ระบบ", use_container_width=True):
            sign_in(email, password)

    with tab_signup:
        new_email = st.text_input("อีเมล", key="reg_email")
        new_password = st.text_input("รหัสผ่าน (6 ตัวขึ้นไป)", type="password", key="reg_pass")
        full_name = st.text_input("ชื่อ-นามสกุล")
        student_id = st.text_input("รหัสนักเรียน")
        
        if st.button("สมัครสมาชิก", use_container_width=True):
            if new_email and new_password and full_name:
                sign_up(new_email, new_password, full_name, student_id)
            else:
                st.warning("กรุณากรอกข้อมูลให้ครบทุกช่อง")

else:
    # --- ส่วนที่ Login สำเร็จแล้ว ---
    st.sidebar.title("เมนู")
    st.sidebar.info(f"ผู้ใช้: {st.session_state.user.email}\nสถานะ: {st.session_state.role}")
    
    if st.sidebar.button("ออกจากระบบ"):
        supabase.auth.sign_out()
        del st.session_state.user
        del st.session_state.role
        st.rerun()

    # แยกหน้าจอตามสิทธิ์
    if st.session_state.role == "admin":
        st.title("🛠️ Admin Dashboard")
        st.write("สวัสดีแอดมิน! คุณสามารถจัดการระบบได้ที่นี่")
    else:
        st.title("🎮 Player Zone")
        st.write("สวัสดีผู้เล่น! เตรียมตัวทำภารกิจกันเลย")
