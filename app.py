import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client

# --- 1. ตั้งค่า Supabase ---
# ตรวจสอบว่าในหมวด Secrets หรือไฟล์ config มี URL และ KEY แล้ว
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase = create_client(URL, KEY)
except:
    st.error("❌ ไม่พบ Supabase Credentials ใน Secrets")
    st.stop()

# --- 2. ฟังก์ชันจัดการสมัครสมาชิก (รับช่วงต่อจาก HTML) ---
def process_registration():
    # ดึงค่าจาก URL Query Parameters
    params = st.query_params
    
    if "reg_user" in params:
        username = params["reg_user"].strip()
        fullname = params["reg_name"]
        phone = params["reg_phone"]
        password = params["reg_pass"]

        try:
            # 1. เช็คชื่อซ้ำ
            check = supabase.table("users").select("username").eq("username", username).execute()
            if check.data:
                st.error(f"❌ ชื่อผู้ใช้ '{username}' มีผู้ใช้งานแล้ว!")
                st.query_params.clear() # ล้างค่าทิ้งเพื่อเริ่มต้นใหม่
                return

            # 2. บันทึกข้อมูล
            user_data = {
                "fullname": fullname,
                "username": username,
                "phone": phone,
                "password": password
            }
            supabase.table("users").insert(user_data).execute()
            
            st.success(f"✅ ยินดีด้วยคุณ {fullname} สมัครสมาชิกสำเร็จ!")
            st.balloons()
            # ล้างค่าเพื่อให้หน้าจอกลับมาเป็นปกติ
            st.query_params.clear()

        except Exception as e:
            st.error(f"⚠️ เกิดข้อผิดพลาดทางเทคนิค: {e}")

# รันระบบตรวจสอบการส่งค่า
process_registration()

# --- 3. UI HTML + CSS + JS (กึ่งกลาง, ไร้ลูกตา, ลืมรหัสหน้าแรก) ---
full_ui = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;700&display=swap');
    body {{ margin: 0; background-color: #f0f2f5; font-family: 'Kanit', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; overflow: hidden; }}
    .container {{ text-align: center; width: 100%; max-width: 400px; padding: 10px; }}
    .main-logo {{ color: #1877f2; font-size: 50px; font-weight: bold; margin-bottom: 5px; letter-spacing: -2px; }}
    .sub-logo {{ color: #000000; font-size: 22px; font-weight: 500; margin-bottom: 25px; }}
    .card {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border: 1px solid #dddfe2; }}
    #signup-box, #forgot-box {{ display: none; }}
    input {{ width: 100%; padding: 14px; margin-bottom: 12px; border: 1px solid #dddfe2; border-radius: 8px; font-size: 16px; box-sizing: border-box; text-align: center; outline: none; }}
    input:focus {{ border-color: #1877f2; }}
    input[type="password"]::-ms-reveal {{ display: none; }}
    .btn {{ width: 100%; border: none; padding: 14px; font-size: 18px; font-weight: bold; border-radius: 8px; cursor: pointer; margin-top: 5px; transition: 0.2s; }}
    .btn-blue {{ background-color: #1877f2; color: white; }}
    .btn-blue:hover {{ background-color: #166fe5; }}
    .btn-green {{ background-color: #42b72a; color: white; width: auto; padding: 12px 30px; }}
    .link-text {{ display: block; color: #1877f2; font-size: 14px; margin: 15px 0; text-decoration: none; cursor: pointer; }}
    .divider {{ border-bottom: 1px solid #dadde1; margin: 20px 0; }}
</style>

<div class="container">
    <div class="main-logo">traffic game</div>
    <div class="sub-logo">เล่นเปลี่ยนรอด</div>
    
    <div class="card" id="login-box">
        <input type="text" id="login_user" placeholder="ชื่อผู้ใช้">
        <input type="password" id="login_pass" placeholder="รหัสผ่าน">
        <button class="btn btn-blue" onclick="alert('ระบบเข้าสู่ระบบกำลังตามมาครับ')">เข้าสู่ระบบ</button>
        <div class="link-text" onclick="showForgot()">ลืมรหัสผ่านใช่หรือไม่?</div>
        <div class="divider"></div>
        <button class="btn btn-green" onclick="showSignup()">สร้างบัญชีใหม่</button>
    </div>

    <div class="card" id="signup-box">
        <h2 style="margin:0 0 20px 0;">สมัครสมาชิก</h2>
        <input type="text" id="reg_fullname" placeholder="ชื่อ-นามสกุล">
        <input type="text" id="reg_user" placeholder="ชื่อผู้ใช้ (อังกฤษ/เลข 6-12 ตัว)">
        <input type="text" id="reg_phone" placeholder="เบอร์โทรศัพท์ (10 หลัก)" maxlength="10">
        <input type="password" id="reg_pass" placeholder="รหัสผ่าน (6-13 ตัว)">
        <input type="password" id="reg_confirm" placeholder="ยืนยันรหัสผ่าน">
        <button class="btn btn-blue" onclick="doRegister()">ลงทะเบียน</button>
        <div class="link-text" onclick="showLogin()">กลับไปหน้าเข้าสู่ระบบ</div>
    </div>

    <div class="card" id="forgot-box">
        <h2 style="margin:0 0 20px 0;">ลืมรหัสผ่าน</h2>
        <input type="text" id="find_user" placeholder="ชื่อผู้ใช้">
        <button class="btn btn-blue">ตรวจสอบ</button>
        <div class="link-text" onclick="showLogin()">กลับไปหน้าเข้าสู่ระบบ</div>
    </div>
</div>

<script>
    function showSignup() {{ document.getElementById('login-box').style.display='none'; document.getElementById('forgot-box').style.display='none'; document.getElementById('signup-box').style.display='block'; }}
    function showLogin() {{ document.getElementById('signup-box').style.display='none'; document.getElementById('forgot-box').style.display='none'; document.getElementById('login-box').style.display='block'; }}
    function showForgot() {{ document.getElementById('login-box').style.display='none'; document.getElementById('signup-box').style.display='none'; document.getElementById('forgot-box').style.display='block'; }}

    function doRegister() {{
        const name = document.getElementById('reg_fullname').value;
        const user = document.getElementById('reg_user').value.trim();
        const phone = document.getElementById('reg_phone').value;
        const pass = document.getElementById('reg_pass').value;
        const confirm = document.getElementById('reg_confirm').value;

        // Validation ขั้นต้น
        if (!name || user.length < 6 || phone.length !== 10 || pass.length < 6) {{
            alert('กรุณากรอกข้อมูลให้ครบถ้วนตามเงื่อนไข');
            return;
        }}
        if (pass !== confirm) {{
            alert('รหัสผ่านไม่ตรงกัน');
            return;
        }}

        // ส่งข้อมูลแบบ Force Redirect ไปที่ Parent Window
        const url = new URL(window.parent.location.origin + window.parent.location.pathname);
        url.searchParams.set('reg_name', name);
        url.searchParams.set('reg_user', user);
        url.searchParams.set('reg_phone', phone);
        url.searchParams.set('reg_pass', pass);
        
        window.parent.location.assign(url.toString());
    }}

    // ล็อคเบอร์โทรตัวเลขเท่านั้น
    document.getElementById('reg_phone').oninput = function() {{
        this.value = this.value.replace(/[^0-9]/g, '');
    }};
</script>
"""

# แสดงผล UI
components.html(full_ui, height=850)
