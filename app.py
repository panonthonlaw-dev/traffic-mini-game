import streamlit as st
import streamlit.components.v1 as components

# 1. ตั้งค่าหน้ากระดาษ
st.set_page_config(page_title="Traffic Game", layout="centered")

# 2. โครงสร้าง HTML + CSS + JS (เน้นความเนียน 100%)
full_ui = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;700&display=swap');

    body {
        margin: 0; padding: 0; background-color: #f0f2f5;
        font-family: 'Kanit', sans-serif;
        display: flex; justify-content: center; align-items: center; height: 100vh;
    }

    .container { text-align: center; width: 100%; max-width: 400px; }
    .main-logo { color: #1877f2; font-size: 50px; font-weight: bold; margin-bottom: 5px; letter-spacing: -2px; }
    .sub-logo { color: #000000; font-size: 22px; font-weight: 500; margin-bottom: 25px; }

    /* การ์ดหลัก */
    .card {
        background: white; padding: 30px; border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border: 1px solid #dddfe2;
        display: block; /* เริ่มต้นแสดงผลหน้า Login */
    }

    /* ซ่อนหน้าสมัครเริ่มต้น */
    #signup-box, #forgot-box { display: none; }

    input {
        width: 100%; padding: 14px; margin-bottom: 12px;
        border: 1px solid #dddfe2; border-radius: 8px;
        font-size: 16px; box-sizing: border-box; text-align: center; outline: none;
    }
    input:focus { border-color: #1877f2; }

    /* ปิดลูกตา */
    input[type="password"]::-ms-reveal, input[type="password"]::-ms-clear { display: none; }

    .btn {
        width: 100%; border: none; padding: 14px; font-size: 18px;
        font-weight: bold; border-radius: 8px; cursor: pointer; margin-top: 5px;
    }
    .btn-blue { background-color: #1877f2; color: white; }
    .btn-green { background-color: #42b72a; color: white; width: auto; padding: 12px 30px; }
    
    .link-text { display: block; color: #1877f2; font-size: 14px; margin: 15px 0; text-decoration: none; cursor: pointer; }
    .divider { border-bottom: 1px solid #dadde1; margin: 20px 0; }
</style>

<div class="container">
    <div class="main-logo">traffic game</div>
    <div class="sub-logo" id="title-text">เล่นเปลี่ยนรอด</div>
    
    <div class="card" id="login-box">
        <input type="text" id="login_user" placeholder="ชื่อผู้ใช้">
        <input type="password" id="login_pass" placeholder="รหัสผ่าน">
        <button class="btn btn-blue" onclick="handleLogin()">เข้าสู่ระบบ</button>
        <div class="link-text" onclick="showForgot()">ลืมรหัสผ่านใช่หรือไม่?</div>
        <div class="divider"></div>
        <button class="btn btn-green" onclick="showSignup()">สร้างบัญชีใหม่</button>
    </div>

    <div class="card" id="signup-box">
        <h2 style="margin-top:0; color:#1c1e21;">สมัครสมาชิก</h2>
        <input type="text" id="reg_user" placeholder="ตั้งชื่อผู้ใช้">
        <input type="password" id="reg_pass" placeholder="ตั้งรหัสผ่าน">
        <input type="password" id="reg_confirm" placeholder="ยืนยันรหัสผ่าน">
        <button class="btn btn-blue" onclick="handleRegister()">ลงทะเบียน</button>
        <div class="link-text" onclick="showLogin()">กลับไปหน้าเข้าสู่ระบบ</div>
    </div>

    <div class="card" id="forgot-box">
        <h2 style="margin-top:0; color:#1c1e21;">ค้นหาบัญชีของคุณ</h2>
        <p style="font-size:14px; color:#606770;">กรุณากรอกชื่อผู้ใช้เพื่อค้นหาบัญชี</p>
        <input type="text" id="find_user" placeholder="ชื่อผู้ใช้">
        <button class="btn btn-blue">ค้นหา</button>
        <div class="link-text" onclick="showLogin()">ยกเลิก</div>
    </div>

    <p style="color: #606770; font-size: 12px; margin-top: 30px;">Traffic Mini Game • ระบบวินัยจราจร</p>
</div>

<script>
    function showSignup() {
        document.getElementById('login-box').style.display = 'none';
        document.getElementById('forgot-box').style.display = 'none';
        document.getElementById('signup-box').style.display = 'block';
    }
    function showLogin() {
        document.getElementById('signup-box').style.display = 'none';
        document.getElementById('forgot-box').style.display = 'none';
        document.getElementById('login-box').style.display = 'block';
    }
    function showForgot() {
        document.getElementById('login-box').style.display = 'none';
        document.getElementById('signup-box').style.display = 'none';
        document.getElementById('forgot-box').style.display = 'block';
    }

    // ฟังก์ชันส่งค่ากลับไป Streamlit (ถ้าต้องการใช้)
    function handleLogin() {
        const user = document.getElementById('login_user').value;
        const pass = document.getElementById('login_pass').value;
        if(user && pass) {
            alert('กำลังตรวจสอบ: ' + user);
        } else {
            alert('กรุณากรอกข้อมูลให้ครบ');
        }
    }
</script>
"""

# แสดงผล HTML
components.html(full_ui, height=800)
