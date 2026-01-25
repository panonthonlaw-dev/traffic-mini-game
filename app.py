import streamlit as st
from supabase import create_client

# --- 1. การตั้งค่าเบื้องต้นและการเชื่อมต่อ ---
st.set_page_config(page_title="ระบบมินิเกมจราจร", page_icon="🚦", layout="centered")

# ดึงค่าจาก Streamlit Secrets
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- 2. ฟังก์ชันช่วยจัดการระบบ (Helper Functions) ---

def get_user_role(user_id):
    """ดึงข้อมูล Role จากตาราง profiles"""
    try:
        response = supabase.table("profiles").select("role").eq("id", user_id).single().execute()
        return response.data["role"] if response.data else "player"
    except:
        return "player"

def sign_in(email, password):
    """ฟังก์ชันเข้าสู่ระบบ"""
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.user:
            st.session_state.user = res.user
            st.session_state.role = get_user_role(res.user.id)
            st.success("เข้าสู่ระบบสำเร็จ!")
            st.rerun()
    except Exception as e:
        st.error(f"เข้าสู่ระบบล้มเหลว: {e}")

def sign_up(email, password, full_name, student_id, role):
    """ฟังก์ชันสมัครสมาชิก"""
    try:
        # 1. สร้างบัญชีใน Auth
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            # 2. บันทึกข้อมูลลงตาราง profiles
            data = {
                "id": res.user.id,
                "full_name": full_name,
                "student_id": student_id,
                "role": role
            }
            supabase.table("profiles").insert(data).execute()
            st.success("สมัครสมาชิกสำเร็จ! กรุณาลองเข้าสู่ระบบ")
    except Exception as e:
        st.error(f"สมัครสมาชิกล้มเหลว: {e}")

# --- 3. ส่วนการควบคุมหน้าจอ (Main Logic) ---

# ตรวจสอบว่า Login หรือยัง
if 'user' not in st.session_state:
    st.title("🚦 ระบบมินิเกมจราจร")
    st.subheader("กรุณาเข้าสู่ระบบเพื่อเริ่มภารกิจ")
    
    tab_login, tab_signup = st.tabs(["เข้าสู่ระบบ", "สมัครสมาชิก"])

    with tab_login:
        email = st.text_input("อีเมล (Email)", key="login_email")
        password = st.text_input("รหัสผ่าน (Password)", type="password", key="login_pass")
        if st.button("ตกลง เข้าสู่ระบบ", use_container_width=True):
            sign_in(email, password)

    with tab_signup:
        st.write("สร้างบัญชีใหม่")
        new_email = st.text_input("อีเมล", key="reg_email")
        new_password = st.text_input("รหัสผ่าน (6 ตัวขึ้นไป)", type="password", key="reg_pass")
        full_name = st.text_input("ชื่อ-นามสกุล")
        student_id = st.text_input("รหัสนักเรียน / รหัสพนักงาน")
        role = st.selectbox("สมัครในฐานะ", ["player", "admin"])
        
        if st.button("สร้างบัญชี", use_container_width=True):
            if new_email and new_password and full_name:
                sign_up(new_email, new_password, full_name, student_id, role)
            else:
                st.warning("กรุณากรอกข้อมูลให้ครบทุกช่อง")

else:
    # --- หน้าจอเมื่อเข้าสู่ระบบสำเร็จ (หลังบ้าน) ---
    st.sidebar.title("เมนูการใช้งาน")
    st.sidebar.info(f"ผู้ใช้: {st.session_state.user.email}\nสถานะ: {st.session_state.role}")
    
    if st.sidebar.button("ออกจากระบบ"):
        supabase.auth.sign_out()
        del st.session_state.user
        del st.session_state.role
        st.rerun()

    # แยกหน้าตาม Role
    if st.session_state.role == "admin":
        st.title("🛠️ หน้าควบคุมสำหรับแอดมิน")
        st.write("ยินดีต้อนรับแอดมิน! คุณสามารถตรวจรูปและให้คะแนนได้ที่นี่")
        # --- เดี๋ยวเราจะเขียนระบบ Admin ตรวจรูปตรงนี้ในขั้นตอนถัดไป ---
        
    else:
        st.title("🎮 หน้าภารกิจผู้เล่น")
        st.write("สวัสดีนักล่าแต้ม! ทำภารกิจวันนี้เพื่อสะสมคะแนนจราจรกันเถอะ")
        # --- เดี๋ยวเราจะเขียนระบบ Player ส่งรูปตรงนี้ในขั้นตอนถัดไป ---
