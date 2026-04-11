import streamlit as st
import pandas as pd
import plotly.express as px
from db_manager import save_diet_record, get_today_records, delete_record

st.set_page_config(page_title="資管飲食助手", layout="wide")
st.title("🥗 飲食紀錄管理系統")

with st.sidebar:
    st.header("⚙️ 個人設定")
    # 讓使用者自訂每日目標，並存入 Session State 中
    daily_goal = st.number_input(
        "設定每日熱量目標 (kcal)", 
        min_value=1200, 
        max_value=4000, 
        value=2000, 
        step=50
    )
    
    st.divider()
    st.info(f"💡 目前設定：{daily_goal} kcal / 天")
    
    st.subheader("⚖️ 體重追蹤")
    current_weight = st.number_input("今日體重 (kg)", min_value=30.0, max_value=200.0, value=70.0, step=0.1)
    if st.button("記錄體重"):
        # 這裡我們先用 success 提示，未來會開新資料表存這筆數據
        st.success(f"已紀錄：{current_weight} kg")

records = get_today_records()
df = pd.DataFrame(records)

if not df.empty:
    total_calories = df['calories'].sum()
    total_protein = df['protein'].sum()
    total_fat = df['fat'].sum()
    total_carbs = df['carbs'].sum()
    remaining_calories = daily_goal - total_calories
else:
    total_calories = total_protein = total_fat = total_carbs = 0
    remaining_calories = daily_goal

st.subheader("🔥 今日營養概覽")
m1, m2, m3, m4 = st.columns(4)
m1.metric("已攝取熱量", f"{total_calories} kcal")
m2.metric("剩餘預算", f"{remaining_calories} kcal", delta_color="inverse")
m3.metric("蛋白質", f"{total_protein} g")
m4.metric("碳水化合物", f"{total_carbs} g")

# 進度條
progress_pct = min(total_calories / daily_goal, 1.0)
st.progress(progress_pct, text=f"今日熱量進度: {int(progress_pct*100)}%")

if total_calories > daily_goal:
    st.warning(f"⚠️ 警告：已超過每日熱量目標 {total_calories - daily_goal} kcal！")

# 使用分頁系統：將「新增紀錄」與「歷史管理」分開
tab1, tab2 = st.tabs(["➕ 新增飲食紀錄", "📋 今日紀錄管理"])

# --- Tab 1: 新增紀錄 ---
with tab1:
    st.subheader("手動紀錄營養成分")

    meal_type = st.radio(
        "這是哪一餐？",
        ["早餐", "午餐", "晚餐", "點心", "其他"],
        horizontal=True  # 讓按鈕橫向排列，節省空間
    )

    st.divider()
    
    # 建立兩欄式佈局，讓介面更緊湊
    col1, col2 = st.columns(2)
    
    with col1:
        food_name = st.text_input("食物名稱", placeholder="例如：香煎雞胸肉")
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

if not df.empty:
    st.divider()
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # 三大營養素圓餅圖 (原本有的)
        nutrients_df = pd.DataFrame({
            "營養素": ["蛋白質", "脂肪", "碳水"],
            "重量": [total_protein, total_fat, total_carbs]
        })
        fig_nutrients = px.pie(nutrients_df, values='重量', names='營養素', title="三大營養素比例")
        st.plotly_chart(fig_nutrients, use_container_width=True)

    with col_chart2:
        # 新增：各餐熱量分佈圖
        # 這裡會根據你昨天的 meal_type 自動分組
        meal_stats = df.groupby('meal_type')['calories'].sum().reset_index()
        fig_meals = px.bar(meal_stats, x='meal_type', y='calories', 
                          title="各餐熱量分佈", 
                          labels={'meal_type': '餐別', 'calories': '總熱量'},
                          color='meal_type')
        st.plotly_chart(fig_meals, use_container_width=True)