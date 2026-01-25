import streamlit as st
import streamlit.components.v1 as components

# ตั้งค่าหน้ากระดาษ
st.set_page_config(page_title="Traffic Game Login", layout="centered")

# --- โค้ด HTML + CSS เพียวๆ (สั่งได้ดั่งใจ 100%) ---
login_form = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;700&display=swap');

    body {
        margin: 0;
        padding: 0;
        background-color: #f0f2f5;
        font-family: 'Kanit', sans-serif;
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
    }

    .container {
        text-align: center;
        width: 100%;
        max-width: 400px;
    }

    .main-logo {
        color: #1877f2;
        font-size: 55px;
        font-weight: bold;
        margin-bottom: 5px;
        letter-spacing: -2px;
    }

    .sub-logo {
        color: #000000;
        font-size: 24px;
        font-weight: 500;
        margin-bottom: 25px;
    }

    .login-card {
        background: white;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        border: 1px solid #dddfe2;
    }

    input {
        width: 100%;
        padding: 14px;
        margin-bottom: 12px;
        border: 1px solid #dddfe2;
        border-radius: 8px;
        font-size: 16px;
        box-sizing: border-box;
        text-align: center;
        outline: none;
    }

    input:focus {
        border-color: #1877f2;
    }

    /* ป้องกันลูกตาโผล่ในเบราว์เซอร์บางตัว */
    input[type="password"]::-ms-reveal,
    input[type="password"]::-ms-clear {
        display: none;
    }

    .login-btn {
        width: 100%;
        background-color: #1877f2;
        color: white;
        border: none;
        padding: 14px;
        font-size: 20px;
        font-weight: bold;
        border-radius: 8px;
        cursor: pointer;
        margin-top: 5px;
    }

    .login-btn:hover { background-color: #166fe5; }

    .forgot-pass {
        display: block;
        color: #1877f2;
        font-size: 14px;
        margin: 15px 0;
        text-decoration: none;
    }

    .divider {
        border-bottom: 1px solid #dadde1;
        margin: 20px 0;
    }

    .signup-btn {
        background-color: #42b72a;
        color: white;
        border: none;
        padding: 12px 25px;
        font-size: 17px;
        font-weight: bold;
        border-radius: 8px;
        cursor: pointer;
        text-decoration: none;
    }

    .signup-btn:hover { background-color: #36a420; }

</style>

<div class="container">
    <div class="main-logo">traffic game</div>
    <div class="sub-logo">เล่นเปลี่ยนรอด</div>
    
    <div class="login-card">
        <form>
            <input type="text" placeholder="ชื่อผู้ใช้" required>
            <input type="password" placeholder="รหัสผ่าน" required>
            <button type="submit" class="login-btn">เข้าสู่ระบบ</button>
        </form>
        
        <a href="#" class="forgot-pass">ลืมรหัสผ่านใช่หรือไม่?</a>
        <div class="divider"></div>
        
        <button class="signup-btn">สร้างบัญชีใหม่</button>
    </div>
    
    <p style="color: #606770; font-size: 12px; margin-top: 30px;">Traffic Mini Game © 2026</p>
</div>
"""

# แสดงผล HTML
components.html(login_form, height=800)
