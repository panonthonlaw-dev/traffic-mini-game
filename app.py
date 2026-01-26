# 🛠️ หน้าหลังบ้าน (Admin) - ฉบับจัดเต็มสำหรับตรวจงาน
elif st.session_state.page == 'admin_dashboard':
    if st.session_state.user is None or st.session_state.user['role'] != 'admin': 
        go_to('login')
    
    st.markdown("<h2 style='color: #1877f2;'>ระบบจัดการหลังบ้าน (Admin)</h2>", unsafe_allow_html=True)
    st.write(f"สวัสดีครับคุณครู: **{st.session_state.user['fullname']}**")
    
    # --- ส่วนที่ 1: ตัวเลือกการกรองงาน ---
    col1, col2 = st.columns(2)
    with col1:
        # เลือกวันที่ต้องการตรวจ (ค่าเริ่มต้นคือวันนี้)
        search_date = st.date_input("เลือกวันที่ตรวจงาน", datetime.now())
        date_str = search_date.strftime("%Y-%m-%d")
    
    with col2:
        # เลือกภารกิจที่ต้องการตรวจ
        all_missions = supabase.table("missions").select("id, title").execute().data
        m_options = {m['title']: m['id'] for m in all_missions}
        selected_m_name = st.selectbox("เลือกภารกิจ", list(m_options.keys()))
        selected_m_id = m_options[selected_m_name]

    st.write("---")

    # --- ส่วนที่ 2: ดึงข้อมูลการส่งงานจาก Supabase ---
    # ดึงรายชื่อเด็กที่ส่งงานตาม วันที่ และ ภารกิจ ที่เลือก
    subs = supabase.table("submissions").select("*, users(student_id, fullname)")\
        .eq("mission_id", selected_m_id)\
        .gte("created_at", date_str)\
        .execute().data

    if not subs:
        st.warning(f"ยังไม่มีนักเรียนส่งงานใน {selected_m_name} ของวันที่ {date_str}")
    else:
        st.success(f"พบนักเรียนส่งงานทั้งหมด {len(subs)} คน")
        
        # --- ส่วนที่ 3: แสดงรายการตรวจงาน ---
        for s in subs:
            std_id = s['users']['student_id']
            std_name = s['users']['fullname']
            
            with st.expander(f"📌 รหัส: {std_id} - {std_name}"):
                # สร้างชื่อไฟล์ตามรูปแบบที่เราตั้งไว้ตอนเด็กส่ง
                target_filename = f"{std_id}_m{selected_m_id}_{date_str}.jpg"
                
                # ค้นหาไฟล์ใน Google Drive
                query = f"name = '{target_filename}' and '{DRIVE_FOLDER_ID}' in parents"
                results = drive_service.files().list(q=query, fields="files(id, name, thumbnailLink)").execute().get('files', [])
                
                if results:
                    file_id = results[0]['id']
                    # ดึงไฟล์มาแสดง (ใช้สไตล์การดึงรูปจาก Drive)
                    st.image(f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000", caption=f"รูปจาก {std_name}")
                    
                    if st.button(f"ให้คะแนน {std_name}", key=f"score_{std_id}"):
                        st.balloons()
                        st.write("บันทึกคะแนนเรียบร้อย! (ระบบคะแนนจะทำในขั้นตอนถัดไป)")
                else:
                    st.error("❌ ไม่พบไฟล์รูปภาพใน Google Drive (อาจเกิดจากชื่อไฟล์ไม่ตรงหรือการอัปโหลดผิดพลาด)")

    st.write("---")
    if st.button("ออกจากระบบ", use_container_width=True): 
        st.session_state.user = None
        go_to('login')
