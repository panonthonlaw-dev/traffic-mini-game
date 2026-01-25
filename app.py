import streamlit as st
from supabase import create_client
import time

# --- 1. ตั้งค่าหน้าเว็บและเชื่อมต่อ Supabase ---
st.set_page_config(page_title="Traffic Game", layout="centered")

try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error("❌ เชื่อมต่อ Supabase ไม่ได้ เช็ค Secrets ด่วน")
    st.stop()

# --- 2. CSS Hack (รักษาหน้าตาเดิมที่พี่ชอบไว้) ---
st.markdown("""
    <style>
        /* 1. จัดกึ่งกลางหน้าจอและบีบความกว้าง */
        .block-container {
            max-width: 450px;
            padding-top: 2rem;
            padding-bottom: 2rem;
            margin: auto;
        }

        /* 2. สร้างกรอบการ์ดสีขาว (Card Effect) */
        .stAppViewContainer {
            background-color: #f0f2f5;
        }
        div[data-testid="stVerticalBlock"] > div {
            background-color: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            border: 1px solid #dddfe2;
        }

        /* 3. จัดตัวหนังสือในช่องกรอกให้กึ่งกลาง */
        .stTextInput input {
            text-align: center;
            border-radius: 8px;
            border: 1px solid #dddfe2;
            padding: 10px;
        }
        
        /* 4. ซ่อนปุ่มลูกตาในช่องรหัสผ่าน (ตามสั่ง) */
        button[aria-label="Show password"] {
            display: none !important;
            visibility: hidden !important;
        }

        /* 5. แต่งปุ่มกดให้เหมือนต้นฉบับ */
        div.stButton > button {
            width: 100%;
            border-radius: 8px;
            font-weight: bold;
            height: 45px;
            border: none;
        }
        
        /* ปุ่มสีฟ้า (Primary) */
        div[data-testid="stVerticalBlock"] button[kind="primary"] {
            background-color: #1877f2;
            color: white;
        }
        div[data-testid="stVerticalBlock"] button[kind="primary"]:hover {
            background-color: #166fe5;
        }

        /* ปุ่มสีเขียว (Secondary -> แปลงเป็นเขียว) */
        div[data-testid="stVerticalBlock"] button[kind="secondary"] {
            background-color: #42b72a;
            color: white;
            border: none;
        }
        div[data-testid="stVerticalBlock"] button[kind="secondary"]:hover {
            background-color: #36a420;
        }

        /* 6. ซ่อน Header/Footer ของ Streamlit */
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* 7. จัดหัวข้อให้สวยงาม */
        .main-title {
            color: #1877f2;
            font-size: 50px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 0px;
            line-height: 1.2;
        }
        .sub-title {
            color: black;
            font-size: 20px;
            text-align: center;
            margin-bottom: 20px;
        }
        .header-text {
            color: #1c1e21;
            text-align: center;
            margin: 0 0 20px 0;
            font-weight: bold;
            font-size: 24px;
        }
        
        /* ลิงก์ลืมรหัสผ่าน */
        .forgot-link {
            text-align: center;
            color: #1877f2;
            font-size: 14px;
            cursor: pointer;
            text-decoration: none;
            display: block;
            margin-top: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. ระบบจัดการ State (สลับหน้า) ---
if 'page' not in st.session_state:
    st.session_state.page = 'login'

def go_to(page_name):
    st.session_state.page = page_name
    st.rerun()

# ==========================================
# 🛑 หน้า 1: LOGIN (หน้าแรก)
# ==========================================
if st.session_state.page == 'login':
    st.markdown('<div class="main-title">traffic game</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">เล่นเปลี่ยนรอด</div>', unsafe_allow_html=True)

    # กล่อง Login
    with st.container():
        user = st.text_input("user", placeholder="ชื่อผู้ใช้", label_visibility="collapsed")
        password = st.text_input("pass", type="password", placeholder="รหัสผ่าน", label_visibility="collapsed")
        
        if st.button("เข้าสู่ระบบ", type="primary"):
            # โค้ดเช็ค Login ใส่ตรงนี้ (เดี๋ยวเราทำต่อ)
            st.info("ระบบกำลังตรวจสอบ...")
        
        # ปุ่มลวงตาเพื่อให้หน้าตาเหมือนเดิม (ใช้ markdown สร้างลิงก์หลอก) -> แต่เราใช้ปุ่มจริงดีกว่า
        if st.button("ลืมรหัสผ่านใช่หรือไม่?"):
             go_to('forgot')

        st.markdown("<hr style='margin: 15px 0; border: 0; border-top: 1px solid #dadde1;'>", unsafe_allow_html=True)
        
        if st.button("สร้างบัญชีใหม่", type="secondary"):
            go_to('signup')

# ==========================================
# 🛑 หน้า 2: SIGNUP (สมัครสมาชิก)
# ==========================================
elif st.session_state.page == 'signup':
    st.markdown('<div class="main-title">traffic game</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">เล่นเปลี่ยนรอด</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="header-text">สมัครสมาชิก</div>', unsafe_allow_html=True)
        
        # ช่องกรอกข้อมูล (Native Streamlit widgets)
        reg_name = st.text_input("name", placeholder="ชื่อ-นามสกุล", label_visibility="collapsed")
        reg_user = st.text_input("reg_user", placeholder="ชื่อผู้ใช้ (อังกฤษ/เลข 6-12 ตัว)", label_visibility="collapsed")
        reg_phone = st.text_input("phone", placeholder="เบอร์โทรศัพท์ (10 หลัก)", max_chars=10, label_visibility="collapsed")
        reg_pass = st.text_input("reg_pass", type="password", placeholder="รหัสผ่าน (6-13 ตัว)", label_visibility="collapsed")
        reg_confirm = st.text_input("confirm", type="password", placeholder="ยืนยันรหัสผ่าน", label_visibility="collapsed")

        # ปุ่มลงทะเบียน (ทำงานจริง 100%)
        if st.button("ลงทะเบียน", type="primary"):
            # 1. Validation Logic (Python ล้วนๆ)
            u_user = reg_user.strip()
            
            if not reg_name or not u_user or not reg_phone or not reg_pass:
                st.error("❌ กรุณากรอกข้อมูลให้ครบทุกช่อง")
            elif " " in reg_user:
                st.error("❌ ชื่อผู้ใช้ห้ามมีเว้นวรรค")
            elif len(u_user) < 6 or len(u_user) > 12:
                st.error("❌ ชื่อผู้ใช้ต้องมี 6-12 ตัวอักษร")
            elif not reg_phone.isdigit() or len(reg_phone) != 10:
                st.error("❌ เบอร์โทรศัพท์ต้องเป็นตัวเลข 10 หลัก")
            elif len(reg_pass) < 6 or len(reg_pass) > 13:
                st.error("❌ รหัสผ่านต้องมี 6-13 ตัวอักษร")
            elif reg_pass != reg_confirm:
                st.error("❌ รหัสผ่านไม่ตรงกัน")
            else:
                # 2. Supabase Logic (ทำงานฝั่ง Server ชัวร์แน่นอน)
                try:
                    # เช็คชื่อซ้ำ
                    check = supabase.table("users").select("username").eq("username", u_user).execute()
                    if check.data:
                        st.error(f"❌ ชื่อผู้ใช้ '{u_user}' มีคนใช้แล้ว")
                    else:
                        # บันทึก
                        data = {
                            "fullname": reg_name,
                            "username": u_user,
                            "phone": reg_phone,
                            "password": reg_pass
                        }
                        supabase.table("users").insert(data).execute()
                        
                        st.success("✅ สมัครสมาชิกสำเร็จ!")
                        st.balloons()
                        time.sleep(2) # รอ 2 วิให้เห็นบอลลูน
                        go_to('login') # เด้งกลับหน้าแรก
                        
                except Exception as e:
                    st.error(f"⚠️ เกิดข้อผิดพลาดระบบ: {e}")

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.button("กลับไปหน้าเข้าสู่ระบบ"):
            go_to('login')

# ==========================================
# 🛑 หน้า 3: FORGOT PASSWORD (ลืมรหัส)
# ==========================================
elif st.session_state.page == 'forgot':
    st.markdown('<div class="main-title">traffic game</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">เล่นเปลี่ยนรอด</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="header-text">ค้นหาบัญชีของคุณ</div>', unsafe_allow_html=True)
        
        find_user = st.text_input("find_user", placeholder="กรอกชื่อผู้ใช้", label_visibility="collapsed")
        
        if st.button("ค้นหา", type="primary"):
            st.info("ฟังก์ชันค้นหากำลังตามมา...")
            
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.button("ยกเลิก"):
            go_to('login')
