import streamlit as st
import pandas as pd
import plotly.express as px
from db_manager import save_diet_record, get_today_records, get_today_summary

st.set_page_config(page_title="AI 飲食助手", layout="wide")

# 1. 先抓取資料 (這決定了圖表的內容)
summary = get_today_summary()
records = get_today_records()
df = pd.DataFrame(records)

st.title("🥗 智能飲食紀錄系統")

# --- 2. 建立左右佈局 ---
# col1 佔 2 份寬度，col2 佔 1 份寬度
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📝 新增紀錄")
    # 這裡就是你的輸入區！
    f_name = st.text_input("食物名稱", key="food_input")
    f_cal = st.number_input("熱量 (kcal)", min_value=0, step=1)
    
    # 讓三個營養素排成一橫列，節省空間
    c1, c2, c3 = st.columns(3)
    f_p = c1.number_input("蛋白質(g)", min_value=0.0)
    f_f = c2.number_input("脂肪(g)", min_value=0.0)
    f_c = c3.number_input("碳水(g)", min_value=0.0)

    if st.button("🚀 存入資料庫"):
        if f_name:
            new_data = {
                "food_name": f_name, "calories": f_cal,
                "protein": f_p, "fat": f_f, "carbs": f_c
            }
            save_diet_record(new_data)
            st.success(f"已存入 {f_name}！")
            st.rerun() # 存完後強制重新整理，圖表就會更新
        else:
            st.error("請輸入食物名稱")

with col2:
    st.subheader("📊 今日營養比例")
    if summary['total_cal'] > 0:
        # 準備畫圖資料
        pie_df = pd.DataFrame({
            "營養素": ["蛋白質", "脂肪", "碳水"],
            "重量 (g)": [summary['total_protein'], summary['total_fat'], summary['total_carbs']]
        })
        fig = px.pie(pie_df, values='重量 (g)', names='營養素', hole=0.4)
        # 調整圖表外觀
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("尚無數據，請先從左側輸入")

# --- 3. 下方顯示歷史明細 ---
st.divider()
st.subheader("🕒 今日紀錄明細")
if not df.empty:
    st.dataframe(df, use_container_width=True)