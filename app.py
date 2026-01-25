import streamlit as st
from supabase import create_client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import re
from PIL import Image
from datetime import datetime

# --- 1. การตั้งค่าหน้าตาแอป (Modern Facebook UI) ---
st.set_page_config(page_title="Traffic Mini Game", page_icon="🚦", layout="centered")

# ล้าง CSS ใหม่ทั้งหมดเพื่อความคลีน
st.markdown("""
    <style>
        /* บังคับพื้นหลังขาวและตัวอักษรดำ */
        .stApp { background-color: #ffffff !important; color: #000000 !important; }
        
        /* ซ่อน Header และ Sidebar */
        header[data-testid="stHeader"] { visibility: hidden; }
        section[data-testid="stSidebar"] { display: none; }
        footer { visibility: hidden; }

        /* ปรับขนาดหน้าจอให้เหมือนแอปมือถือ */
        .block-container { max-width: 450px !important; padding-top: 1rem !important; }

        /* จัดการหัวข้อโลโก้ */
        .main-title { color: #1877f2; font-size: 42px; font-weight: bold; text-align: center; margin-bottom: 0px; }
        .sub-title { color: #606770; font-size: 16px; text-align: center; margin-bottom: 20px; }

        /* ตกแต่ง Card ช่องกรอกข้อมูล */
        [data-testid="stVerticalBlock"] > div:has(div.stTabs) {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
            border: 1px solid #e4e6eb;
        }

        /* บังคับตัวหนังสือใน Tabs ให้ดำชัดเจน */
        .stTabs [data-baseweb="tab-list"] { background-color: #f0f2f5; border-radius: 10px; padding: 4px; }
        .stTabs [data-baseweb="tab"] p { color: #65676b !important; font-weight: 600 !important; }
        .stTabs [data-baseweb="tab"][aria-selected="true"] p { color: #1877f2 !important; }

        /* ปรับแต่งช่องกรอก (Input) ให้เรียบเนียน ไม่เลอะเทอะ */
        input {
            color: #000000 !important;
            background-color: #f5f6f7 !important;
            border: 1px solid #dddfe2 !important;
            border-radius: 8px !important;
            padding: 12px !important;
        }
        label { color: #000000 !important; font-weight: 600 !important; margin-bottom: 4px !important; }

        /* ปุ่มกดสไตล์ Facebook */
        button, .stButton>button {
            background-color: #1877f2 !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            border: none !important;
            font-size: 18px !important;
            font-weight: bold !important;
            height: 48px !important;
            width: 100% !important;
            margin-top: 10px;
        }
        button:hover { background-color: #166fe5 !important; }

        /* ปุ่มสมัครสมาชิก (สีเขียว) */
        .green-btn button { background-color: #42b72a !important; }
        .green-btn button:hover { background-color: #36a420 !important; }
        
        .stAlert { border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. การเชื่อมต่อ Services ---
@st.cache_resource
def init_services():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    s_key = st.secrets["SUPABASE_SERVICE_KEY"]
    return create_client(url, key), create_client(url, s_key)

supabase, supabase_admin = init_services()

def init_drive():
    info = st.secrets["gcp_service_account"]
    creds = service_account.Credentials.from_service_account_info(info)
    return build('drive', 'v3', credentials=creds)

# --- 3. ระบบ Logic ตรวจสอบความถูกต้อง ---

def format_email(user_id):
    return f"{user_id.strip().lower()}@traffic.com"

def validate_data(u_id, u_pw, s_id, phone):
    if len(u_id) < 6 or not re.match("^[a-zA-Z0-9]*$", u_id):
        return False, "❌ UserID ต้องเป็นภาษาอังกฤษ/ตัวเลข 6 ตัวขึ้นไป"
    if not re.match("^[a-zA-Z0-9]*$", u_pw):
        return False, "❌ รหัสผ่านต้องเป็นภาษาอังกฤษหรือตัวเลขเท่านั้น"
    if not s_id.isdigit():
        return False, "❌ รหัสนักเรียนต้องเป็นตัวเลขเท่านั้น"
    if not re.match("^0(6|8|9)[0-9]{8}$", phone):
        return False, "❌ เบอร์โทรต้องมี 10 หลัก ขึ้นต้นด้วย 06, 08 หรือ 09"
    return True, ""

def upload_image(file, user_id):
    try:
        drive_service = init_drive()
        img = Image.open(file).convert("RGB")
        img.thumbnail((1024, 1024))
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=80)
        buf.seek(0)
        meta = {'name': f"{user_id}_{datetime.now().strftime('%H%M%S')}.jpg", 'parents': [st.secrets["GDRIVE_FOLDER_ID"]]}
        media = MediaIoBaseUpload(buf, mimetype='image/jpeg', resumable=True)
        res = drive_service.files().create(body=meta, media_body=media, fields='id').execute()
        return res.get('id')
    except: return None

# --- 4. การแสดงผล UI ---

if 'user' not in st.session_state:
    st.markdown("<div class='main-title'>traffic game</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>บันทึกวินัยจราจรและสะสมแต้มความดี</div>", unsafe_allow_html=True)
    
    tab_l, tab_s, tab_f = st.tabs(["🔐 เข้าสู่ระบบ", "📝 สมัครสมาชิก", "🔑 ลืมรหัสผ่าน"])
    
    with tab_l:
        l_id = st.text_input("ชื่อผู้ใช้", placeholder="UserID", key="l_id")
        l_pw = st.text_input("รหัสผ่าน", type="password", placeholder="Password", key="l_pw")
        if st.button("เข้าสู่ระบบ", key="btn_login"):
            try:
                res = supabase.auth.sign_in_with_password({"email": format_email(l_id), "password": l_pw})
                if res.user:
                    r = supabase.table("profiles").select("role").eq("id", res.user.id).single().execute()
                    st.session_state.user, st.session_state.role = res.user, r.data['role']
                    st.rerun()
            except: st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    with tab_s:
        s_id_in = st.text_input("ตั้ง UserID", key="s_uid")
        s_pw_in = st.text_input("ตั้งรหัสผ่าน", type="password", key="s_pw")
        s_name = st.text_input("ชื่อ-นามสกุลจริง")
        s_sid = st.text_input("รหัสนักเรียน")
        s_phone = st.text_input("เบอร์โทรศัพท์ (10 หลัก)")
        st.markdown("<div class='green-btn'>", unsafe_allow_html=True)
        if st.button("สร้างบัญชีใหม่", key="btn_signup"):
            if all([s_id_in, s_pw_in, s_name, s_sid, s_phone]):
                is_v, msg = validate_data(s_id_in, s_pw_in, s_sid, s_phone)
                if not is_v: st.error(msg)
                else:
                    try:
                        res = supabase.auth.sign_up({"email": format_email(s_id_in), "password": s_pw_in})
                        if res.user:
                            supabase.table("profiles").insert({
                                "id": res.user.id, "username": s_id_in.lower(), "full_name": s_name, 
                                "student_id": s_sid, "phone_number": s_phone, "role": "player", "password_plain": s_pw_in
                            }).execute()
                            st.success("✅ สมัครสำเร็จ! กรุณาไปที่แท็บ 'เข้าสู่ระบบ'")
                    except: st.error("❌ ชื่อนี้มีคนใช้ไปแล้ว")
            else: st.warning("กรุณากรอกข้อมูลให้ครบ")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_f:
        st.markdown("### กู้คืนรหัสผ่าน")
        f_u = st.text_input("UserID", key="f_u")
        f_s = st.text_input("รหัสนักเรียน", key="f_s")
        f_p = st.text_input("เบอร์โทรศัพท์", key="f_p")
        f_pw = st.text_input("รหัสผ่านใหม่", type="password", key="f_pw")
        if st.button("ตั้งรหัสผ่านใหม่", key="btn_reset"):
            if all([f_u, f_s, f_p, f_pw]) and re.match("^[a-zA-Z0-9]*$", f_pw):
                try:
                    check = supabase.table("profiles").select("id").eq("username", f_u.lower()).eq("student_id", f_s).eq("phone_number", f_p).single().execute()
                    if check.data:
                        supabase_admin.auth.admin.update_user_by_id(check.data['id'], {"password": f_pw})
                        supabase.table("profiles").update({"password_plain": f_pw}).eq("id", check.data['id']).execute()
                        st.success("✅ เปลี่ยนรหัสผ่านสำเร็จ!")
                    else: st.error("❌ ข้อมูลไม่ถูกต้อง")
                except: st.error("❌ ไม่พบข้อมูลผู้ใช้")

else:
    # --- หน้า Dashboard (เมื่อ Login แล้ว) ---
    prof_data = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).single().execute().data
    
    col_h, col_o = st.columns([0.7, 0.3])
    col_h.markdown(f"👤 **{prof_data['username']}** | {prof_data['role']}")
    if col_o.button("Logout", key="btn_out"):
        supabase.auth.sign_out(); st.session_state.clear(); st.rerun()

    st.divider()
    if st.session_state.role == "admin":
        st.title("🛠️ แอดมินจัดการงาน")
        # โค้ดส่วนแอดมิน...
    else:
        st.title(f"สวัสดีคุณ {prof_data['username']} 👋")
        c1, c2 = st.columns(2)
        c1.metric("🪙 คะแนน", prof_data.get('total_points', 0))
        c2.metric("🎖️ ระดับ", prof_data.get('rank_title', 'ผู้เริ่มต้น'))
        
        # ส่วนภารกิจ...
