import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client

# --- 1. เชื่อมต่อ Supabase (ดึงค่าจาก Secrets) ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# --- 2. ระบบดักรับข้อมูลจากปุ่มลงทะเบียน ---
def handle_registration():
    # ใช้ st.query_params (เวอร์ชันใหม่ไม่ต้องมีวงเล็บ)
    params = st.query_params
    
    # ถ้ามีค่า 'reg_user' โผล่มาที่ URL แปลว่ามีการกดปุ่มลงทะเบียนมา
    if "reg_user" in params:
        u_name = params["reg_name"]
        u_user = params["reg_user"]
        u_phone = params["reg_phone"]
        u_pass = params["reg_pass"]

        try:
            # เช็คชื่อซ้ำแบบพื้นฐาน
            res = supabase.table("users").select("username").eq("username", u_user).execute()
            if res.data:
                st.warning(f"⚠️ ชื่อผู้ใช้ '{u_user}' มีคนใช้แล้วครับพี่!")
            else:
                # บันทึกลงตาราง users
                supabase.table("users").insert({
                    "fullname": u_name,
                    "username": u_user,
                    "phone": u_phone,
                    "password": u_pass
                }).execute()
                
                st.success(f"✅ สมัครสำเร็จ! ข้อมูลเข้า Supabase แล้วครับคุณ {u_name}")
                st.balloons()

            # ล้างค่า URL ทันทีเพื่อป้องกันการบันทึกซ้ำ
            st.query_params.clear()
            
        except Exception as e:
            st.error(f"⚠️ ติดปัญหาที่ฐานข้อมูล: {e}")

# รันระบบดักข้อมูลก่อนแสดงผลหน้าจอ
handle_registration()

# --- 3. UI HTML + CSS + JS (จัดกึ่งกลาง ไร้ลูกตา ตามสั่งเป๊ะ) ---
full_ui = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;700&display=swap');
    body {{ margin: 0; background-color: #f0f2f5; font-family: 'Kanit', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
    .container {{ text-align: center; width: 100%; max-width: 400px; padding: 20px; }}
    .main-logo {{ color: #1877f2; font-size: 50px; font-weight: bold; margin-bottom: 5px; }}
    .sub-logo {{ color: #000000; font-size: 22px; margin-bottom: 25px; }}
    .card {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border: 1px solid #dddfe2; }}
    #signup-box, #forgot-box {{ display: none; }}
    input {{ width: 100%; padding: 14px; margin-bottom: 12px; border: 1px solid #dddfe2; border-radius: 8px; font-size: 16px; text-align: center; box-sizing: border-box; outline: none; }}
    input[type="password"]::-ms-reveal {{ display: none; }}
    .btn {{ width: 100%; border: none; padding: 14px; font-size: 18px; font-weight: bold; border-radius: 8px; cursor: pointer; margin-top: 5px; }}
    .btn-blue {{ background-color: #1877f2; color: white; }}
    .btn-green {{ background-color: #42b72a; color: white; width: auto; padding: 12px 30px; }}
    .link-text {{ display: block; color: #1877f2; font-size: 14px; margin: 15px 0; cursor: pointer; }}
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
        <input type="text" id="reg_user" placeholder="ชื่อผู้ใช้ (6-12 ตัว)">
        <input type="text" id="reg_phone" placeholder="เบอร์โทรศัพท์ (10 หลัก)">
        <input type="password" id="reg_pass" placeholder="รหัสผ่าน (6-13 ตัว)">
        <input type="password" id="reg_confirm" placeholder="ยืนยันรหัสผ่าน">
        <button class="btn btn-blue" onclick="saveData()">ลงทะเบียน</button>
        <div class="link-text" onclick="showLogin()">กลับไปหน้าแรก</div>
    </div>

    <div class="card" id="forgot-box">
        <h2 style="margin:0 0 20px 0;">ลืมรหัสผ่าน</h2>
        <input type="text" id="find_user" placeholder="ชื่อผู้ใช้">
        <button class="btn btn-blue">ตรวจสอบ</button>
        <div class="link-text" onclick="showLogin()">กลับไปหน้าแรก</div>
    </div>
</div>

<script>
    function showSignup() {{ document.getElementById('login-box').style.display='none'; document.getElementById('signup-box').style.display='block'; }}
    function showLogin() {{ document.getElementById('signup-box').style.display='none'; document.getElementById('forgot-box').style.display='none'; document.getElementById('login-box').style.display='block'; }}
    function showForgot() {{ document.getElementById('login-box').style.display='none'; document.getElementById('forgot-box').style.display='block'; }}

    function saveData() {{
        const name = document.getElementById('reg_fullname').value;
        const user = document.getElementById('reg_user').value.trim();
        const phone = document.getElementById('reg_phone').value;
        const pass = document.getElementById('reg_pass').value;
        const confirm = document.getElementById('reg_confirm').value;

        if (!name || user.length < 6 || phone.length !== 10 || pass !== confirm) {{
            alert('กรุณากรอกข้อมูลให้ครบและรหัสผ่านต้องตรงกัน');
            return;
        }}

        // วิธีที่ชัวร์ที่สุด: บังคับเปลี่ยน URL ของหน้าหลัก (Top level)
        const currentUrl = window.top.location.origin + window.top.location.pathname;
        const nextUrl = currentUrl + "?reg_name=" + encodeURIComponent(name) + 
                        "&reg_user=" + encodeURIComponent(user) + 
                        "&reg_phone=" + encodeURIComponent(phone) + 
                        "&reg_pass=" + encodeURIComponent(pass);
        
        window.top.location.href = nextUrl;
    }}
</script>
"""

components.html(full_ui, height=850)
