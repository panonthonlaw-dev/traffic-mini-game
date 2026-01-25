import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client

# --- 1. ตั้งค่าการเชื่อมต่อ Supabase ---
# กรุณาใส่ URL และ Key ของคุณใน secrets หรือใส่ตรงนี้
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# --- 2. ฟังก์ชันสำหรับเช็คชื่อซ้ำและบันทึกลง Supabase ---
def register_user(fullname, username, phone, password):
    # ลบช่องว่างหน้าหลัง (Trim) อีกรอบเพื่อความชัวร์
    username = username.strip()
    
    # เช็คชื่อผู้ใช้ซ้ำในฐานข้อมูล
    check_user = supabase.table("users").select("username").eq("username", username).execute()
    
    if check_user.data:
        return "duplicate" # ชื่อซ้ำ
    
    # บันทึกข้อมูลลงตาราง users
    data = {
        "fullname": fullname,
        "username": username,
        "phone": phone,
        "password": password # แนะนำให้ hash รหัสผ่านในอนาคตเพื่อความปลอดภัย
    }
    try:
        supabase.table("users").insert(data).execute()
        return "success"
    except Exception as e:
        return str(e)

# --- 3. ส่วนการรับข้อมูลจาก HTML ---
# ใช้ query params เป็นท่อส่งข้อมูลสั้นๆ จาก JS กลับมา Python
query_params = st.query_params

if "reg_user" in query_params:
    status = register_user(
        query_params["reg_name"],
        query_params["reg_user"],
        query_params["reg_phone"],
        query_params["reg_pass"]
    )
    
    if status == "success":
        st.success("บันทึกข้อมูลสำเร็จ!")
        st.query_params.clear() # ล้างค่าทิ้งเพื่อไม่ให้รันซ้ำ
    elif status == "duplicate":
        st.error("ชื่อผู้ใช้ี้มีคนใช้แล้ว!")
    else:
        st.error(f"เกิดข้อผิดพลาด: {status}")

# --- 4. โครงสร้าง UI (HTML + JS) ---
full_ui = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;700&display=swap');
    body {{ margin: 0; background-color: #f0f2f5; font-family: 'Kanit', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
    .container {{ text-align: center; width: 100%; max-width: 400px; padding: 20px; }}
    .main-logo {{ color: #1877f2; font-size: 50px; font-weight: bold; margin-bottom: 5px; letter-spacing: -2px; }}
    .sub-logo {{ color: #000000; font-size: 22px; font-weight: 500; margin-bottom: 25px; }}
    .card {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border: 1px solid #dddfe2; }}
    #signup-box {{ display: none; }}
    input {{ width: 100%; padding: 14px; margin-bottom: 12px; border: 1px solid #dddfe2; border-radius: 8px; font-size: 16px; box-sizing: border-box; text-align: center; outline: none; }}
    input:focus {{ border-color: #1877f2; }}
    input[type="password"]::-ms-reveal {{ display: none; }}
    .btn {{ width: 100%; border: none; padding: 14px; font-size: 18px; font-weight: bold; border-radius: 8px; cursor: pointer; margin-top: 5px; }}
    .btn-blue {{ background-color: #1877f2; color: white; }}
    .btn-green {{ background-color: #42b72a; color: white; width: auto; padding: 12px 30px; }}
    .link-text {{ display: block; color: #1877f2; font-size: 14px; margin: 15px 0; text-decoration: none; cursor: pointer; }}
    .divider {{ border-bottom: 1px solid #dadde1; margin: 20px 0; }}
    .error-msg {{ color: #d32f2f; font-size: 13px; margin-top: -10px; margin-bottom: 10px; display: none; }}
</style>

<div class="container">
    <div class="main-logo">traffic game</div>
    <div class="sub-logo">เล่นเปลี่ยนรอด</div>
    
    <div class="card" id="login-box">
        <input type="text" id="login_user" placeholder="ชื่อผู้ใช้">
        <input type="password" id="login_pass" placeholder="รหัสผ่าน">
        <button class="btn btn-blue">เข้าสู่ระบบ</button>
        <div class="divider"></div>
        <button class="btn btn-green" onclick="showSignup()">สร้างบัญชีใหม่</button>
    </div>

    <div class="card" id="signup-box">
        <h2 style="margin:0 0 20px 0; color:#1c1e21;">สมัครสมาชิก</h2>
        <input type="text" id="reg_fullname" placeholder="ชื่อ-นามสกุล">
        <input type="text" id="reg_user" placeholder="ชื่อผู้ใช้ (อังกฤษ/เลข 6-12 ตัว)">
        <input type="text" id="reg_phone" placeholder="เบอร์โทรศัพท์ (10 หลัก)" maxlength="10">
        <input type="password" id="reg_pass" placeholder="รหัสผ่าน (6-13 ตัว)">
        <input type="password" id="reg_confirm" placeholder="ยืนยันรหัสผ่าน">
        <button class="btn btn-blue" onclick="validateSignup()">ลงทะเบียน</button>
        <div class="link-text" onclick="showLogin()">กลับไปหน้าเข้าสู่ระบบ</div>
    </div>
</div>

<script>
    function showSignup() {{ document.getElementById('login-box').style.display = 'none'; document.getElementById('signup-box').style.display = 'block'; }}
    function showLogin() {{ document.getElementById('signup-box').style.display = 'none'; document.getElementById('login-box').style.display = 'block'; }}

    function validateSignup() {{
        const name = document.getElementById('reg_fullname').value;
        const userRaw = document.getElementById('reg_user').value;
        const user = userRaw.trim();
        const phone = document.getElementById('reg_phone').value;
        const pass = document.getElementById('reg_pass').value;
        const confirm = document.getElementById('reg_confirm').value;

        if (userRaw !== user) {{ alert('ห้ามมีเว้นวรรคหน้าหลังชื่อผู้ใช้'); return; }}
        if (user.length < 6 || user.length > 12) {{ alert('ชื่อผู้ใช้ต้องมี 6-12 ตัว'); return; }}
        if (phone.length !== 10) {{ alert('เบอร์โทรต้องมี 10 หลัก'); return; }}
        if (pass !== confirm) {{ alert('รหัสผ่านไม่ตรงกัน'); return; }}

        // --- ส่งข้อมูลกลับไปหา Python ผ่าน URL ---
        const url = new URL(window.location.href);
        url.searchParams.set('reg_name', name);
        url.searchParams.set('reg_user', user);
        url.searchParams.set('reg_phone', phone);
        url.searchParams.set('reg_pass', pass);
        window.parent.location.href = url.href;
    }}
</script>
"""

components.html(full_ui, height=900)
