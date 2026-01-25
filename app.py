import streamlit as st
import streamlit.components.v1 as components

# 1. ตั้งค่าหน้ากระดาษ
st.set_page_config(page_title="Traffic Game", layout="centered")

# 2. โครงสร้าง HTML + CSS + JS (เน้นความเป๊ะเรื่องเบอร์โทร 10 หลัก)
full_ui = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;700&display=swap');

    body {
        margin: 0; padding: 0; background-color: #f0f2f5;
        font-family: 'Kanit', sans-serif;
        display: flex; justify-content: center; align-items: center; min-height: 100vh;
    }

    .container { text-align: center; width: 100%; max-width: 400px; padding: 20px; }
    .main-logo { color: #1877f2; font-size: 50px; font-weight: bold; margin-bottom: 5px; letter-spacing: -2px; }
    .sub-logo { color: #000000; font-size: 22px; font-weight: 500; margin-bottom: 25px; }

    .card {
        background: white; padding: 30px; border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); border: 1px solid #dddfe2;
    }

    #signup-box { display: none; }

    input {
        width: 100%; padding: 14px; margin-bottom: 12px;
        border: 1px solid #dddfe2; border-radius: 8px;
        font-size: 16px; box-sizing: border-box; text-align: center; outline: none;
    }
    input:focus { border-color: #1877f2; }
    
    /* ปิดลูกตาดูรหัสผ่านถาวร */
    input[type="password"]::-ms-reveal, input[type="password"]::-ms-clear { display: none; }

    .btn {
        width: 100%; border: none; padding: 14px; font-size: 18px;
        font-weight: bold; border-radius: 8px; cursor: pointer; margin-top: 5px;
    }
    .btn-blue { background-color: #1877f2; color: white; }
    .btn-green { background-color: #42b72a; color: white; width: auto; padding: 12px 30px; }
    
    .link-text { display: block; color: #1877f2; font-size: 14px; margin: 15px 0; text-decoration: none; cursor: pointer; }
    .divider { border-bottom: 1px solid #dadde1; margin: 20px 0; }
    
    .error-msg { color: #d32f2f; font-size: 13px; margin-top: -10px; margin-bottom: 10px; display: none; }
</style>

<div class="container">
    <div class="main-logo">traffic game</div>
    <div class="sub-logo">เล่นเปลี่ยนรอด</div>
    
    <div class="card" id="login-box">
        <input type="text" id="login_user" placeholder="ชื่อผู้ใช้">
        <input type="password" id="login_pass" placeholder="รหัสผ่าน">
        <button class="btn btn-blue" onclick="handleLogin()">เข้าสู่ระบบ</button>
        <div class="link-text">ลืมรหัสผ่านใช่หรือไม่?</div>
        <div class="divider"></div>
        <button class="btn btn-green" onclick="showSignup()">สร้างบัญชีใหม่</button>
    </div>

    <div class="card" id="signup-box">
        <h2 style="margin-top:0; color:#1c1e21;">สมัครสมาชิก</h2>
        
        <input type="text" id="reg_fullname" placeholder="ชื่อ-นามสกุล">
        <div id="err_name" class="error-msg">กรุณากรอกชื่อ-นามสกุลให้ถูกต้อง</div>

        <input type="text" id="reg_user" placeholder="ชื่อผู้ใช้ (อังกฤษ/เลข 6-12 ตัว)">
        <div id="err_user" class="error-msg">ชื่อผู้ใช้ต้องเป็นอังกฤษ/ตัวเลข 6-12 ตัว</div>

        <input type="text" id="reg_phone" placeholder="เบอร์โทรศัพท์ (เลข 10 หลัก)" maxlength="10">
        <div id="err_phone" class="error-msg">กรุณากรอกเบอร์โทรศัพท์เป็นตัวเลข 10 หลัก</div>
        
        <input type="password" id="reg_pass" placeholder="รหัสผ่าน (6-13 ตัว)">
        <div id="err_pass" class="error-msg">รหัสผ่านต้องเป็นอังกฤษ/ตัวเลข 6-13 ตัว</div>

        <input type="password" id="reg_confirm" placeholder="ยืนยันรหัสผ่าน">
        <div id="err_match" class="error-msg">รหัสผ่านไม่ตรงกัน</div>

        <button class="btn btn-blue" onclick="validateSignup()">ลงทะเบียน</button>
        <div class="link-text" onclick="showLogin()">กลับไปหน้าเข้าสู่ระบบ</div>
    </div>

    <p style="color: #606770; font-size: 12px; margin-top: 30px;">Traffic Mini Game • Safety First</p>
</div>

<script>
    function showSignup() {
        document.getElementById('login-box').style.display = 'none';
        document.getElementById('signup-box').style.display = 'block';
    }
    function showLogin() {
        document.getElementById('signup-box').style.display = 'none';
        document.getElementById('login-box').style.display = 'block';
    }

    function validateSignup() {
        const name = document.getElementById('reg_fullname').value;
        const user = document.getElementById('reg_user').value;
        const phone = document.getElementById('reg_phone').value;
        const pass = document.getElementById('reg_pass').value;
        const confirm = document.getElementById('reg_confirm').value;

        // --- เงื่อนไขการตรวจสอบ ---
        const userRegex = /^[a-zA-Z0-9]{6,12}$/;
        const passRegex = /^[a-zA-Z0-9]{6,13}$/;
        const phoneRegex = /^[0-9]{10}$/; // ตัวเลขล้วน 10 หลัก
        const nameRegex = /^[a-zA-Zก-ฮะ-์\s]+$/;

        let isValid = true;

        // ล้าง Error เก่า
        document.querySelectorAll('.error-msg').forEach(el => el.style.display = 'none');

        if (!nameRegex.test(name)) { document.getElementById('err_name').style.display = 'block'; isValid = false; }
        if (!userRegex.test(user)) { document.getElementById('err_user').style.display = 'block'; isValid = false; }
        if (!phoneRegex.test(phone)) { document.getElementById('err_phone').style.display = 'block'; isValid = false; }
        if (!passRegex.test(pass)) { document.getElementById('err_pass').style.display = 'block'; isValid = false; }
        if (pass !== confirm) { document.getElementById('err_match').style.display = 'block'; isValid = false; }

        if (isValid) {
            alert('ลงทะเบียนสำเร็จสำหรับผู้ใช้: ' + user);
            // พร้อมส่งข้อมูลไปบันทึกลงฐานข้อมูล
        }
    }

    // ป้องกันการพิมพ์ตัวอักษรลงในช่องเบอร์โทร
    document.getElementById('reg_phone').oninput = function() {
        this.value = this.value.replace(/[^0-9]/g, '');
    };
</script>
"""

# แสดงผล HTML
components.html(full_ui, height=900, scrolling=True)
