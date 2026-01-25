import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client

# --- 1. ตั้งค่าการเชื่อมต่อ Supabase ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# --- 2. ฟังก์ชันบันทึกข้อมูล ---
def register_user(fullname, username, phone, password):
    username = username.strip()
    check_user = supabase.table("users").select("username").eq("username", username).execute()
    if check_user.data:
        return "duplicate"
    data = {"fullname": fullname, "username": username, "phone": phone, "password": password}
    try:
        supabase.table("users").insert(data).execute()
        return "success"
    except Exception as e:
        return str(e)

# รับค่าจาก JavaScript
query_params = st.query_params
if "reg_user" in query_params:
    status = register_user(
        query_params["reg_name"], query_params["reg_user"],
        query_params["reg_phone"], query_params["reg_pass"]
    )
    if status == "success":
        st.success("ลงทะเบียนสำเร็จ!")
        st.query_params.clear()
    elif status == "duplicate":
        st.error("ชื่อผู้ใช้นี้มีคนใช้แล้ว!")
    else:
        st.error(f"Error: {status}")

# --- 3. โครงสร้าง UI (HTML + CSS + JS) ---
full_ui = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;700&display=swap');
    body {{ margin: 0; background-color: #f0f2f5; font-family: 'Kanit', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
    .container {{ text-align: center; width: 100%; max-width: 400px; padding: 20px; }}
    .main-logo {{ color: #1877f2; font-size: 50px; font-weight: bold; margin-bottom: 5px; letter-spacing: -2px; }}
    .sub-logo {{ color: #000000; font-size: 22px; font-weight: 500; margin-bottom: 25px; }}
    .card {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border: 1px solid #dddfe2; }}
    #signup-box, #forgot-box {{ display: none; }}
    input {{ width: 100%; padding: 14px; margin-bottom: 12px; border: 1px solid #dddfe2; border-radius: 8px; font-size: 16px; box-sizing: border-box; text-align: center; outline: none; }}
    input:focus {{ border-color: #1877f2; }}
    input[type="password"]::-ms-reveal {{ display: none; }}
    .btn {{ width: 100%; border: none; padding: 14px; font-size: 18px; font-weight: bold; border-radius: 8px; cursor: pointer; margin-top: 5px; }}
    .btn-blue {{ background-color: #1877f2; color: white; }}
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
        <button class="btn btn-blue">เข้าสู่ระบบ</button>
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
        <button class="btn btn-blue" onclick="validateSignup()">ลงทะเบียน</button>
        <div class="link-text" onclick="showLogin()">กลับไปหน้าเข้าสู่ระบบ</div>
    </div>

    <div class="card" id="forgot-box">
        <h2 style="margin:0 0 20px 0;">ลืมรหัสผ่าน</h2>
        <p style="font-size:14px; color:#606770;">กรุณากรอกชื่อผู้ใช้เพื่อตรวจสอบ</p>
        <input type="text" id="find_user" placeholder="ชื่อผู้ใช้">
        <button class="btn btn-blue">ตรวจสอบ</button>
        <div class="link-text" onclick="showLogin()">กลับไปหน้าเข้าสู่ระบบ</div>
    </div>

    <p style="color: #606770; font-size: 12px; margin-top: 30px;">Traffic Mini Game © 2026</p>
</div>

<script>
    function showSignup() {{ document.getElementById('login-box').style.display='none'; document.getElementById('forgot-box').style.display='none'; document.getElementById('signup-box').style.display='block'; }}
    function showLogin() {{ document.getElementById('signup-box').style.display='none'; document.getElementById('forgot-box').style.display='none'; document.getElementById('login-box').style.display='block'; }}
    function showForgot() {{ document.getElementById('login-box').style.display='none'; document.getElementById('signup-box').style.display='none'; document.getElementById('forgot-box').style.display='block'; }}

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
        if (pass.length < 6 || pass.length > 13) {{ alert('รหัสผ่านต้องมี 6-13 ตัว'); return; }}
        if (pass !== confirm) {{ alert('รหัสผ่านไม่ตรงกัน'); return; }}

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
