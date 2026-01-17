import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 配置与初始化 ---
DB_FILE = "gathering_data.csv"
ADMIN_PASSWORD = "2026admin"

# --- 生成带天气标注的日期列表 ---
def get_date_options():
    raw_dates = pd.date_range(start="2026-01-19", end="2026-02-15")
    options = []
    for d in raw_dates:
        d_str = d.strftime('%Y-%m-%d')
        day = d.day
        month = d.month
        # 根据要求标注天气
        if month == 1:
            if day in [19, 20, 21]:
                d_str += "（雪）"
            elif day in [24, 25, 26]:
                d_str += "（雨夹雪）"
            elif day == 28:
                d_str += "（小雨）"
        options.append(d_str)
    return options

DATE_OPTIONS = get_date_options()

st.set_page_config(page_title="2026春节聚会征集", layout="centered")

def init_db():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=["姓名", "有空日期", "期望地点", "聚会建议", "提交时间"])
        df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

def save_data(name, dates, locations, suggestion):
    df = pd.read_csv(DB_FILE, encoding='utf-8-sig')
    new_data = {
        "姓名": name,
        "有空日期": ",".join(dates),
        "期望地点": ",".join(locations),
        "聚会建议": suggestion,
        "提交时间": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    if name in df['姓名'].values:
        df.loc[df['姓名'] == name, ["有空日期", "期望地点", "聚会建议", "提交时间"]] = \
            [new_data["有空日期"], new_data["期望地点"], new_data["聚会建议"], new_data["提交时间"]]
    else:
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

# --- UI 界面 ---
init_db()

st.title("🧧 2026 春节聚会意向征集")
st.info("大家填一下有空的时间和想去的地点，方便汇总定计划~")

# --- 用户填写区 ---
with st.expander("📝 点击填写我的意向", expanded=True):
    user_name = st.text_input("1. 您的姓名", placeholder="请输入名字")
    
    # 更改：日期标题标注（可多选），并引用带天气的选项
    selected_days = st.multiselect(
        "2. 哪些日期你有空？（可多选）",
        options=DATE_OPTIONS,
        help="点击选择框可以勾选多个日期"
    )
    
    selected_locs = st.multiselect(
        "3. 想在哪里聚？",
        options=["长阳", "宜昌"],
        default=["长阳", "宜昌"]
    )
    
    user_suggestion = st.text_area("4. 聚会建议 / 想吃的 / 想玩的", placeholder="比如：想吃火锅、想去唱歌...")

    if st.button("🚀 提交意向", use_container_width=True):
        if not user_name or not selected_days:
            st.error("姓名和日期是必填项哦！")
        else:
            save_data(user_name, selected_days, selected_locs, user_suggestion)
            st.success("提交成功！")
            st.balloons()

# --- 管理员模式 ---
with st.sidebar:
    st.header("⚙️ 管理端")
    admin_mode = st.checkbox("我是管理员")
    if admin_mode:
        pwd = st.text_input("验证密码", type="password")
        if pwd == ADMIN_PASSWORD:
            st.session_state['admin_auth'] = True
        elif pwd:
            st.error("密码错误")

if admin_mode and st.session_state.get('admin_auth'):
    st.divider()
    st.subheader("📊 汇总统计")
    df_all = pd.read_csv(DB_FILE, encoding='utf-8-sig')

    if not df_all.empty:
        csv_buffer = df_all.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="📥 下载完整原始数据 (CSV)",
            data=csv_buffer,
            file_name="春节聚会统计_2026.csv",
            mime="text/csv"
        )
        
        st.write("📅 **大家最有空的日期：**")
        all_dates = []
        for d_str in df_all['有空日期'].dropna():
            all_dates.extend(str(d_str).split(','))
        
        if all_dates:
            date_counts = pd.Series(all_dates).value_counts().reset_index()
            date_counts.columns = ['日期', '人数']
            # 按日期本身排序，而不是按人数
            st.dataframe(date_counts.sort_values("日期"), hide_index=True, use_container_width=True)

        st.write("📍 **地点偏好统计：**")
        all_locs = []
        for l_str in df_all['期望地点'].dropna():
            all_locs.extend(str(l_str).split(','))
        if all_locs:
            st.bar_chart(pd.Series(all_locs).value_counts())

        st.write("💬 **大家想说：**")
        for _, row in df_all.iterrows():
            suggestion = str(row['聚会建议']).strip()
            if suggestion and suggestion != 'nan':
                st.chat_message("user").write(f"**{row['姓名']}**: {suggestion}")

        st.divider()
        if st.button("🔥 清空所有记录", type="secondary"):
            pd.DataFrame(columns=["姓名", "有空日期", "期望地点", "聚会建议", "提交时间"]).to_csv(DB_FILE, index=False, encoding='utf-8-sig')
            st.rerun()
    else:
        st.info("暂无数据。")