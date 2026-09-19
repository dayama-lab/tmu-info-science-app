import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="シラバス・時間割作成ツール", layout="wide")

@st.cache_data
def load_data():
    script_dir = os.path.dirname(__file__)
    csv_path = os.path.join(script_dir, "syllabus_tmu_ver2.csv")
    if not os.path.exists(csv_path):
        csv_path = "syllabus_tmu_ver2.csv"
    return pd.read_csv(csv_path)

df = load_data()

CATEGORY_COL = "科目区分" if "科目区分" in df.columns else df.columns[0]
SUB_CATEGORY_COL = "区分詳細" if "区分詳細" in df.columns else None
SUBJECT_COL = "科目名" if "科目名" in df.columns else df.columns[1]

ID_COL = next((c for c in df.columns if any(k in str(c) for k in ["ID", "コード", "番号", "id"])), None)
if not ID_COL:
    df["_generated_id"] = df.index.astype(str)
    ID_COL = "_generated_id"

DAY_COL = next((c for c in df.columns if "曜日" in str(c) or str(c) == "曜日"), None)
PERIOD_COL = next((c for c in df.columns if "時限" in str(c) or str(c) == "時限"), None)
SEMESTER_COL = next((c for c in df.columns if any(k in str(c) for k in ["開講期", "学期", "期"])), None)

def reset_select(key_to_reset):
    st.session_state[key_to_reset] = "-- 未選択 --"

st.title("シラバス・時間割作成ツール")

target_year = st.radio(
    "**表示・選択する対象学年を選んでください**",
    options=["1年", "2年", "3年", "4年"],
    horizontal=True
)

st.divider()

days = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "他"]
periods = [1, 2, 3, 4, 5, 6]

if SEMESTER_COL and SEMESTER_COL in df.columns:
    unique_sems = df[SEMESTER_COL].dropna().astype(str).str.strip().unique().tolist()
    semesters = [s for s in unique_sems if s and s != "nan"]
    if not semesters:
        semesters = ["前期", "後期", "通年", "集中"]
else:
    semesters = ["前期", "後期", "通年", "集中"]

total_credits = 0
category_credits = {}

for period in periods + [0]:
    for day in days:
        for sem in semesters:
            key = f"select_{day}_{period}限_{sem}"
            selected_id = st.session_state.get(key, "-- 未選択 --")
            
            if selected_id and selected_id != "-- 未選択 --":
                match = df[df[ID_COL].astype(str) == str(selected_id)]
                if not match.empty:
                    info = match.iloc[0]
                    credit_val = info.get("単位数", info.get("単位", 2))
                    try:
                        c = float(credit_val)
                    except (ValueError, TypeError):
                        c = 2.0
                    
                    total_credits += c
                    
                    cat = str(info.get(CATEGORY_COL, "その他")).strip()
                    if cat and cat != "nan":
                        category_credits[cat] = category_credits.get(cat, 0.0) + c

st.subheader("📊 年間取得単位数（全学期・全区分 合算）")

if category_credits:
    metrics_cols = st.columns(len(category_credits) + 1)
    metrics_cols[0].metric(
        label="合計取得単位数", 
        value=f"{int(total_credits) if total_credits.is_integer() else total_credits} 単位"
    )
    for idx, (cat_name, credits) in enumerate(category_credits.items()):
        val_str = f"{int(credits) if credits.is_integer() else credits} 単位"
        metrics_cols[idx + 1].metric(label=f"【{cat_name}】", value=val_str)
else:
    st.metric(label="合計取得単位数", value="0 単位")
    st.caption("※ 時間割から科目を選択すると、全学期を合算した単位数がリアルタイムで集計されます。")

st.divider()

header_cols = st.columns([1, 2, 2, 2, 2, 2, 2])
header_cols[0].write("**時限**")
for i, day in enumerate(days):
    header_cols[i + 1].write(f"**{day}**")

for period in periods:
    row_cols = st.columns([1, 2, 2, 2, 2, 2, 2])
    row_cols[0].write(f"**{period}限**")
    
    for i, day in enumerate(days):
        with row_cols[i + 1]:
            current_period_str = "0" if day == "他" and period == 1 else str(period)
            
            if day == "他" and period > 1:
                continue

            for sem in semesters:
                filtered_df = df.copy()
            
                if target_year in filtered_df.columns:
                    filtered_df = filtered_df[pd.to_numeric(filtered_df[target_year], errors='coerce').fillna(0) == 1]

                if SEMESTER_COL and SEMESTER_COL in df.columns:
                    filtered_df = filtered_df[filtered_df[SEMESTER_COL].astype(str).str.contains(sem, na=False)]
                
                if DAY_COL and DAY_COL in df.columns:
                    if day == "他":
                        filtered_df = filtered_df[filtered_df[DAY_COL].astype(str).str.contains("他", na=False)]
                    else:
                        day_short = day.replace("曜日", "")
                        filtered_df = filtered_df[filtered_df[DAY_COL].astype(str).str.contains(day_short, na=False)]
                
                if PERIOD_COL and PERIOD_COL in df.columns:
                    filtered_df = filtered_df[filtered_df[PERIOD_COL].astype(str).str.contains(current_period_str, na=False)]

                option_map = {}
                for _, row in filtered_df.iterrows():
                    subj_name = str(row[SUBJECT_COL])
                    course_id = str(row[ID_COL])
                    
                    label = f"{subj_name} [ID:{course_id}]" if ID_COL != "_generated_id" else subj_name
                    option_map[label] = course_id

                options_labels = list(option_map.keys())
                
                if len(options_labels) > 0:
                    st.caption(f"【{sem}】")
                    select_key = f"select_{day}_{period}限_{sem}"
                    course_options = ["-- 未選択 --"] + options_labels
                    
                    current_id = st.session_state.get(select_key, "-- 未選択 --")
                    current_label = "-- 未選択 --"
                    for lbl, cid in option_map.items():
                        if cid == current_id:
                            current_label = lbl
                            break

                    selected_label = st.selectbox(
                        label=f"{day}{period}限{sem}",
                        options=course_options,
                        index=course_options.index(current_label) if current_label in course_options else 0,
                        key=f"sb_{select_key}",
                        label_visibility="collapsed"
                    )
                    
                    if selected_label != "-- 未選択 --":
                        selected_id = option_map[selected_label]
                        st.session_state[select_key] = selected_id
                        
                        match = df[df[ID_COL].astype(str) == selected_id]
                        if not match.empty:
                            info = match.iloc[0]
                            selected_course = info[SUBJECT_COL]
                            cat = str(info.get(CATEGORY_COL, "")).strip()
                            credit = info.get("単位数", info.get("単位", ""))
                            
                            sub_cat = ""
                            if SUB_CATEGORY_COL and SUB_CATEGORY_COL in info:
                                raw_sub = str(info[SUB_CATEGORY_COL]).strip()
                                if raw_sub and raw_sub not in ["nan", "-", "None"]:
                                    sub_cat = raw_sub
                            
                            with st.container(border=True):
                                st.markdown(f"**{selected_course}**")
                                
                                details = []
                                if cat and cat != "nan":
                                    details.append(cat)
                                if sub_cat:
                                    details.append(sub_cat)
                                if pd.notna(credit) and str(credit) != "":
                                    details.append(f"{credit}単位")
                                
                                if details:
                                    st.caption(" / ".join(details))
                                
                                st.button(
                                    "削除",
                                    key=f"btn_{select_key}",
                                    on_click=reset_select,
                                    args=(select_key,)
                                )
                    else:
                        st.session_state[select_key] = "-- 未選択 --"
