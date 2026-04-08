import streamlit as st
import pandas as pd
import plotly.express as px
from db_manager import save_diet_record, get_today_records, delete_record

st.set_page_config(page_title="資管飲食助手", layout="wide")
st.title("🥗 飲食紀錄管理系統")

# 使用分頁系統：將「新增紀錄」與「歷史管理」分開
tab1, tab2 = st.tabs(["➕ 新增飲食紀錄", "📋 今日紀錄管理"])

# --- Tab 1: 新增紀錄 ---
with tab1:
    st.subheader("手動紀錄營養成分")
    
    # 建立兩欄式佈局，讓介面更緊湊
    col1, col2 = st.columns(2)
    
    with col1:
        food_name = st.text_input("食物名稱", placeholder="例如：香煎雞胸肉")
        # 新增任務：餐別下拉選單
        meal_type = st.selectbox("選擇餐別", ["早餐", "午餐", "晚餐", "點心", "宵夜"])
        calories = st.number_input("熱量 (kcal)", min_value=0, step=10)
        
    with col2:
        protein = st.number_input("蛋白質 (g)", min_value=0, step=1)
        fat = st.number_input("脂肪 (g)", min_value=0, step=1)
        carbs = st.number_input("碳水化合物 (g)", min_value=0, step=1)

    if st.button("儲存今日紀錄", use_container_width=True):
        if food_name:
            # 呼叫更新後的 save_diet_record，傳入 meal_type
            save_diet_record(food_name, calories, protein, fat, carbs, meal_type)
            st.success(f"✅ 已成功存入 {meal_type}：{food_name}")
            st.rerun()  # 立即重新整理畫面顯示新資料
        else:
            st.error("請輸入食物名稱！")

# --- Tab 2: 紀錄管理 ---
with tab2:
    st.subheader("今日飲食明細")
    records = get_today_records()
    
    if records:
        df = pd.DataFrame(records)
        
        # 顯示資料表 (排除 ID 不顯示在主表，讓畫面整潔)
        display_df = df[['meal_type', 'food_name', 'calories', 'protein', 'fat', 'carbs']]
        st.dataframe(display_df, use_container_width=True)
        
        st.divider()
        
        # 實作刪除功能
        st.subheader("🗑️ 刪除錯誤紀錄")
        # 讓使用者透過 ID 選擇要刪除哪一筆
        delete_id = st.selectbox(
            "選擇要刪除的紀錄 ID", 
            df['id'].tolist(),
            format_func=lambda x: f"ID: {x} - {df[df['id']==x]['food_name'].values[0]}"
        )
        
        if st.button("確認刪除這筆紀錄"):
            delete_record(delete_id)
            st.warning(f"已刪除 ID 為 {delete_id} 的紀錄")
            st.rerun()
    else:
        st.info("今天還沒有任何紀錄喔，快去第一分頁新增吧！")