import streamlit as st
from supabase import create_client
import re

# --- 1. ตั้งค่าหน้าตาแอปและการเชื่อมต่อ ---
st.set_page_config(page_title="ระบบมินิเกมจราจร", page_icon="🚦", layout="centered")

@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- 2. ฟังก์ชันช่วยจัดการ (Logic) ---

def format_email(user_id):
    """แปลง UserID เป็นอีเมลเสมือน"""
    return f"{user_id.lower()}@traffic.game"

def is_valid_userid(user_id):
    """ตรวจสอบเงื่อนไข ID: อังกฤษ/เลข, > 6 ตัว"""
    if len(user_id) <= 6:
        return False, "❌ UserID ต้องมีความยาวมากกว่า 6 ตัวอักษร"
    if not re.match("^[a-zA-Z0-9]*$", user_id):
        return False, "❌ UserID ต้องเป็นภาษาอังกฤษหรือตัวเลขเท่านั้น (ห้ามเว้นวรรค/อักขระพิเศษ)"
    return True, ""

def get_user_role(user_id):
    try:
        response = supabase.table("profiles").select("role").eq("id", user_id).single().execute()
        return response.data["role"] if response.data else "player"
    except:
        return "player"

# --- 3. ฟังก์ชันระบบ Login / Signup ---

def sign_in(user_id, password):
    virtual_email = format_email(user_id)
    try:
        res = supabase.auth.sign_in_with_password({"email": virtual_email, "password": password})
        if res.user:
            st.session_state.user = res.user
            st.session_state.role = get_user_role(res.user.id)
            st.success(f"ยินดีต้อนรับคุณ {user_id}!")
            st.rerun()
    except Exception as e:
        st.error("UserID หรือรหัสผ่านไม่ถูกต้อง")

def sign_up(user_id, password, full_name, student_id):
    # ตรวจสอบรูปแบบ ID ก่อน
    valid, msg = is_valid_userid(user_id)
    if not valid:
        st.error(msg)
        return

    virtual_email = format_email(user_id)
    try:
        # สมัครสมาชิกในระบบ Auth
        res = supabase.auth.sign_up({"email": virtual_email, "password": password})
        if res.user:
            # บันทึกข้อมูลเพิ่มในตาราง profiles
            data = {
                "id": res.user.id,
                "full_name": full_name,
                "student_id": student_id,
                "role": "player" 
            }
            supabase.table("profiles").insert(data).execute()
            st.success(f"✅ สมัครสำเร็จ! ใช้ UserID: {user_id} เข้าใช้งานได้เลย")
        else:
            st.error("UserID นี้อาจถูกใช้งานไปแล้ว")
    except Exception as e:
        if "already registered" in str(e).lower():
            st.error("❌ UserID นี้มีผู้ใช้งานแล้ว")
        else:
            st.error(f"เกิดข้อผิดพลาด: {e}")

# --- 4. ส่วนการแสดงผลบนหน้าจอ (UI) ---

if 'user' not in st.session_state:
    st.title("🚦 ระบบมินิเกมจราจร")
    
    # สร้างลิ้นชัก (Tabs) ตรงนี้เพื่อป้องกัน NameError
    tab_login, tab_signup = st.tabs(["🔐 เข้าสู่ระบบ", "📝 สมัครสมาชิก"])

    with tab_login:
        u_id = st.text_input("UserID", key="login_uid")
        u_pass = st.text_input("รหัสผ่าน", type="password", key="login_pass")
        if st.button("ตกลง เข้าสู่ระบบ", use_container_width=True):
            if u_id and u_pass:
                sign_in(u_id, u_pass)
            else:
                st.warning("กรุณากรอกข้อมูลให้ครบ")

    with tab_signup:
        st.info("💡 UserID: ภาษาอังกฤษ/ตัวเลข, มากกว่า 6 ตัว และห้ามซ้ำ")
        new_uid = st.text_input("ตั้ง UserID", key="reg_uid")
        new_pass = st.text_input("ตั้งรหัสผ่าน (6 ตัวขึ้นไป)", type="password", key="reg_pass")
        new_name = st.text_input("ชื่อ-นามสกุล")
        new_sid = st.text_input("รหัสนักเรียน/รหัสพนักงาน")
        
        if st.button("สร้างบัญชีผู้เล่น", use_container_width=True):
            if new_uid and new_pass and new_name and new_sid:
                sign_up(new_uid, new_pass, new_name, new_sid)
            else:
                st.warning("กรุณากรอกข้อมูลให้ครบทุกช่อง")

else:
    # --- หน้าจอหลัง Login สำเร็จ ---
    st.sidebar.title("เมนูการใช้งาน")
    display_name = st.session_state.user.email.split('@')[0]
    st.sidebar.info(f"ผู้ใช้: {display_name}\nสถานะ: {st.session_state.role}")
    
    if st.sidebar.button("ออกจากระบบ"):
        supabase.auth.sign_out()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    if st.session_state.role == "admin":
        st.header("🛠️ หน้าควบคุมแอดมิน")
        st.write("สวัสดีครับแอดมิน คุณพร้อมจะตรวจงานหรือยัง?")
    else:
        st.header("🎮 พื้นที่ผู้เล่น")
        st.write(f"สวัสดีคุณ {display_name} เริ่มทำภารกิจกันเถอะ!")
