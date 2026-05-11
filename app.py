import streamlit as st
import pandas as pd
import os
import json
from google import genai
import plotly.express as px
from db_manager import save_diet_record, get_today_records, delete_record, get_setting, update_setting, save_exercise_record, get_today_exercise, get_weekly_summary, get_weekly_nutrition

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "diet_system.db")



st.set_page_config(page_title="飲食管理系統", layout="wide")
st.title("飲食紀錄管理系統")

initial_goal = int(get_setting('daily_calorie_goal', 2000))

burned_calories = get_today_exercise()

# 側邊欄功能
with st.sidebar:
    st.header("⚙️ 個人設定")
    # 讓使用者自訂每日目標，並存入 Session State 中
    new_goal = st.number_input(
        "設定每日熱量目標 (kcal)", 
        min_value=1200, 
        max_value=4000, 
        value=initial_goal,
        step=50
    )

    if new_goal != initial_goal:
        update_setting('daily_calorie_goal', new_goal)
        st.toast(f"✅ 目標已更新為 {new_goal} kcal")
    
    st.divider()

    st.subheader("⚖️ 體重追蹤")
    current_weight = st.number_input("今日體重 (kg)", min_value=30.0, max_value=200.0, value=70.0, step=0.1)
    if st.button("記錄體重"):
        # 這裡我們先用 success 提示，未來會開新資料表存這筆數據
        st.success(f"已紀錄：{current_weight} kg")
    
    st.subheader("⚖️ BMI 計算器")
    height = st.number_input("身高 (cm)", value=170.0)
    weight = st.number_input("體重 (kg)", value=65.0)
    if height > 0:
        bmi = weight / ((height/100)**2)
        st.write(f"您的 BMI 為: **{bmi:.1f}**")
#--------------------------------------------------------------------------------------------------------------------------------------------------------

records = get_today_records()
df = pd.DataFrame(records)

if not df.empty:
    total_calories = df['calories'].sum()
    total_protein = df['protein'].sum()
    total_fat = df['fat'].sum()
    total_carbs = df['carbs'].sum()
    remaining_calories = new_goal - total_calories + burned_calories
else:
    total_calories = total_protein = total_fat = total_carbs = 0
    remaining_calories = new_goal

st.subheader("🔥 今日營養概覽")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("已攝取熱量", f"{total_calories} kcal")
m2.metric("今日運動消耗", f"{burned_calories} kcal")
m3.metric("剩餘預算", f"{remaining_calories} kcal", delta_color="inverse")
m4.metric("蛋白質", f"{total_protein} g")
m5.metric("碳水化合物", f"{total_carbs} g")

# 進度條
progress_pct = min((total_calories - burned_calories) / new_goal, 1.0)
st.progress(progress_pct, text=f"今日熱量進度: {int(progress_pct*100)}%")

if total_calories > new_goal:
    st.warning(f"⚠️ 警告：已超過每日熱量目標 {total_calories - new_goal} kcal！")
elif remaining_calories < 300 and remaining_calories > 0:
    st.info("💡 剩餘額度不多了，晚餐建議吃清淡一點喔！")

# 使用分頁系統：將「新增紀錄」與「歷史管理」分開
tab1, tab2, tab3, tab4 = st.tabs(["➕ 新增飲食紀錄", "📋 今日紀錄管理", "⚽️運動記錄", "📊圖表分析"])

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

    # --- AI 分析與存檔區塊 ---
    with st.container(border=True):
        st.subheader("AI 飲食自動分析")
        
        # 使用者輸入區
        user_input = st.text_input(
            "找不到飲養成分嗎？問問AI吧！", 
            key="ai_input",
            placeholder="例如：一份炒米粉、一顆蘋果跟兩片甜不辣"
        )
        
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            # 按下開始分析，只負責向 AI 拿資料
            analyze_btn = st.button("開始分析", type="primary")

    # 1. 觸發 AI 分析邏輯
    if analyze_btn:
        if not user_input:
            st.warning("請先輸入內容喔！")
        else:
            with st.spinner("正在為您計算多項食物營養..."):
                try:
                    prompt = f"""
                    你是一位專業營養師。請分析以下飲食內容中的每一項食物，最後回傳一個總和的 JSON 格式。
                    要求回傳格式（嚴格遵守）：
                    {{"food_item": "食物清單簡述", "calories": 總熱量數字, "protein": 總蛋白質數字, "fat": 總脂肪數字, "carbs": 總碳水數字}}
                    
                    飲食內容：{user_input}
                    """

                    response = client.models.generate_content(
                        model="gemini-3-flash-preview",
                        contents=prompt,
                        config={'response_mime_type': 'application/json'}
                    )

                    # 解析並存入 session_state 暫存
                    raw_text = response.text.strip()
                    # 簡單清理可能的 Markdown 標籤
                    if "```" in raw_text:
                        raw_text = raw_text.split("```")[1].replace("json", "").strip()
                    
                    # 將結果存入暫存，防止按鈕刷新後消失
                    st.session_state.ai_diet_data = json.loads(raw_text)
                    st.success("✅ AI 分析完成，請確認下方數據：")

                except Exception as e:
                    st.error(f"❌ 分析失敗：{e}")

    # 2. 顯示預覽結果與「確認存檔」按鈕
    # 判斷暫存區是否有資料，有的話才顯示預覽卡片
    if "ai_diet_data" in st.session_state:
        diet_data = st.session_state.ai_diet_data
        
        with st.container(border=True):
            st.markdown(f"🔍 **分析結果預覽**：{diet_data.get('food_item', '未命名')}")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("總熱量", f"{diet_data.get('calories', 0)} kcal")
            c2.metric("蛋白質", f"{diet_data.get('protein', 0)} g")
            c3.metric("脂肪", f"{diet_data.get('fat', 0)} g")
            c4.metric("碳水", f"{diet_data.get('carbs', 0)} g")
            
            # 讓使用者在存檔前可以自選餐別
            meal_choice = st.selectbox("確認這筆紀錄的餐別：", ["早餐", "午餐", "晚餐", "點心", "其他"], index=0)

            # 真正的存檔按鈕
            if st.button("確認正確，存入資料庫", use_container_width=True):
                save_diet_record(
                    diet_data['food_item'], 
                    diet_data['calories'], 
                    diet_data['protein'], 
                    diet_data['fat'], 
                    diet_data['carbs'], 
                    meal_choice
                )
                st.toast(f"🚀 紀錄已存入 {meal_choice}！")
                
                # 存完檔後清除暫存資料，讓介面變回乾淨狀態
                del st.session_state.ai_diet_data
                st.rerun()
                
        if st.button("取消分析並清除", key="cancel_ai"):
            del st.session_state.ai_diet_data
            st.rerun()

    st.caption("本系統採用 Gemini 3 Flash Preview 模型進行分析")
#--------------------------------------------------------------------------------------------------------------------------------------------------------

# --- Tab 2: 紀錄管理 ---
with tab2:
    st.subheader("🍗 蛋白質攝取水位追蹤")

    # 1. 計算目標水位 (體重 * 1.5)
    # 這裡的 weight 來自你側邊欄的 st.number_input("今日體重 (kg)")
    protein_target = weight * 1.5
    
    # 2. 建立水位圖數據
    # 確保 total_protein 已經在前面計算好了
    current_p = float(total_protein)
    
    # 準備 Plotly 數據
    water_level_data = pd.DataFrame({
        "類別": ["蛋白質攝取量"],
        "當前量": [current_p],
        "目標量": [protein_target]
    })

    # 3. 繪製直方圖 (水位效果)
    fig_water = px.bar(
        water_level_data, 
        x="類別", 
        y="當前量",
        range_y=[0, max(protein_target * 1.2, current_p * 1.1)], # 讓 y 軸稍微高出目標，視覺較舒適
        text_auto=True,
        title=f"今日目標：{protein_target:.1f} g (體重 {weight}kg × 1.5)",
        color_discrete_sequence=["#3366ff"] # 水位顏色
    )

    # 4. 加入目標橫線 (目標水位線)
    fig_water.add_hline(
        y=protein_target, 
        line_dash="dash", 
        line_color="red", 
        annotation_text=f"目標線: {protein_target:.1f}g", 
        annotation_position="top right"
    )

    # 優化圖表樣式
    fig_water.update_layout(
        height=400,
        yaxis_title="蛋白質重量 (g)",
        xaxis_title="",
        showlegend=False
    )

    st.plotly_chart(fig_water, use_container_width=True)

    # 顯示文字回饋
    if current_p < protein_target:
        st.info(f"還差 **{protein_target - current_p:.1f} g** 蛋白質就能達標，加油！")
    else:
        st.success(f"🎊 已達成目標！超標 {(current_p - protein_target):.1f} g")
    st.divider()
    st.subheader("🗓️ 今日飲食明細管理")

    # 從資料庫撈取今日資料
    today_items = get_today_records()

    if today_items:
        # 建立標題列
        h_col1, h_col2, h_col3, h_col4 = st.columns([3, 2, 2, 1])
        h_col1.caption("食物名稱")
        h_col2.caption("熱量 (kcal)")
        h_col3.caption("三大營養素 (P/F/C)")
        h_col4.caption("操作")

        for item in today_items:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                # 顯示基本資訊
                col1.write(f"**{item['food_name']}** ({item['meal_type']})")
                col2.write(f"{item['calories']} kcal")
                col3.write(f"{item['protein']}/{item['fat']}/{item['carbs']}")
                
                # 刪除按鈕
                # 使用 key=f"del_{item['id']}" 確保每個按鈕的 ID 唯一
                if col4.button("🗑️", key=f"del_{item['id']}"):
                    delete_record(item['id'])
                    st.success(f"已刪除 {item['food_name']}")
                    st.rerun() # 立即重新整理頁面，讓圖表和清單同步更新
    else:
        st.info("今天還沒有任何飲食紀錄，快去上方輸入吧！")   

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
#--------------------------------------------------------------------------------------------------------------------------------------------------------

with tab3:
    st.subheader("新增運動消耗")


    net_calories = total_calories - burned_calories

    st.subheader("🔥 今日營養概覽")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("已攝取熱量", f"{total_calories} kcal")
    m2.metric("運動消耗", f"{burned_calories} kcal")
    m3.metric("淨熱量", f"{net_calories} kcal")
    m4.metric("剩餘預算", f"{new_goal - net_calories} kcal")

    col_ex1, col_ex2 = st.columns(2)

    with col_ex1:
        ex_name = st.text_input("運動項目", placeholder="例如：慢跑、重訓、游泳")
        ex_dur = st.number_input("持續時間（分鐘）", min_value=0, step=5)

    with col_ex2:
        ex_burn = st.number_input("消耗熱量（kcal）", min_value=0, step=10)
        st.caption("💡 提示：一般慢跑 30 分鐘約消耗 200-300 kcal")
    
    if st.button("儲存運動記錄", use_container_width=True):
        if ex_burn and ex_dur > 0:
            save_exercise_record(ex_name, ex_burn, ex_dur)
            st.success(f"✅ 已成功紀錄：{ex_name}，消耗 {ex_burn} kcal！")
            st.rerun()
        elif not ex_name:
            st.error("請輸入運動項目名稱！")
        else:
            st.warning("請輸入有效的消耗熱量。")

    st.divider()

    st.subheader("今日運動明細")
    burned_calories = get_today_exercise()
    st.info(f"今日累計運動消耗：**{burned_calories}** kcal")
#--------------------------------------------------------------------------------------------------------------------------------------------------------

with tab4:
    st.header("飲養分布圖")
    st.divider()
    st.subheader("📈 過去七天熱量趨勢")


    # 呼叫 db_manager 裡的函數
    weekly_df = get_weekly_summary()

    if not weekly_df.empty:
    
        weekly_df.columns = ['時間', '熱量']
        
        fig_trend = px.line(
            weekly_df, 
            x='時間', 
            y='熱量', 
            markers=True,
            title="過去七天熱量趨勢"
        )
        st.plotly_chart(fig_trend)
    else:
        st.info("尚無趨勢數據。")

    st.divider()
    st.subheader("🍕 過去七天營養比例")

    nutrition_df = get_weekly_nutrition()

    st.write(nutrition_df)

    # 1. 營養圓餅圖部分 (確保使用我們在 db_manager 改好的 get_weekly_nutrition)
    nutrition_df = get_weekly_nutrition()

    if not nutrition_df.empty:
        # PostgreSQL 的欄位名稱通常會維持小寫
        p = nutrition_df['total_protein'].iloc[0]
        f = nutrition_df['total_fat'].iloc[0]
        c = nutrition_df['total_carbs'].iloc[0]
        
        total_weight = p + f + c
        
        if total_weight > 0:
            pie_data = pd.DataFrame({
                "營養素": ["蛋白質", "脂肪", "碳水化合物"],
                "重量 (g)": [float(p), float(f), float(c)] # 轉為 float 確保 Plotly 讀取
            })
            
            fig_pie = px.pie(
                pie_data, 
                values='重量 (g)', 
                names='營養素', 
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("💡 過去七天尚無營養數據。")
    else:
        st.error("無法從 PostgreSQL 讀取數據，請檢查資料庫連線。")

