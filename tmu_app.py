import streamlit as st
import pandas as pd

# ページの設定（ワイドモード）
st.set_page_config(page_title="都立大 情報科学 時間割・単位計算ツール", layout="wide")

# PC表示を維持しつつ、スマホ（画面幅768px以下）のみ横崩れを防止するレスポンシブCSS
st.markdown("""
<style>
/* スマホなどの狭い画面（768px以下）でのみ横スクロールと崩れ防止を適用 */
@media (max-width: 768px) {
    [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        overflow-x: auto;
    }
    [data-testid="column"] {
        min-width: 100px !important;
        padding: 0 2px !important;
    }
    div[data-baseweb="select"] {
        font-size: 11px !important;
    }
}

/* ラベルやヘッダーの表示設定 */
.period-header {
    font-weight: bold;
    text-align: center;
    padding: 4px 0;
}
.sub-label {
    font-size: 11px;
    color: #666666;
    margin-bottom: -4px;
}
</style>
""", unsafe_allow_html=True)

st.title("📚 シラバス・時間割作成ツール")

# シラバスデータの読み込み
@st.cache_data
def load_data():
    df = pd.read_csv("syllabus_tmu.csv")
    if '科目区分' in df.columns:
        df['区分'] = df['科目区分']
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"syllabus_tmu.csv の読み込みに失敗しました: {e}")
    st.stop()

# 対象学年フィルター
st.write("### 表示・選択する対象学年を選んでください")
target_year = st.radio("学年", ["1年", "2年", "3年", "4年"], horizontal=True)

# 選択された学年列に値が入っている科目を抽出
if target_year in df.columns:
    filtered_df = df[df[target_year].notna() & (df[target_year].astype(str).str.strip() != "")]
else:
    filtered_df = df.copy()

st.markdown("---")

# 単位数の集計表示（PC元通りの大きなレイアウト）
st.subheader("📊 年間取得単位数（全学期・全区分 合算）")

total_credits = 0
selected_summary = []

for key, course_name in st.session_state.items():
    if isinstance(course_name, str) and course_name != "-- 未選択 --":
        match_row = df[df["科目名"] == course_name]
        if not match_row.empty:
            try:
                credit = float(match_row.iloc[0]["単位数"])
            except (ValueError, TypeError):
                credit = 0.0
                
            total_credits += credit
            cat = match_row.iloc[0]["区分"] if "区分" in match_row.columns else "-"
            selected_summary.append({
                "科目名": course_name,
                "単位数": credit,
                "区分": cat
            })

st.metric("合計取得単位数", f"{int(total_credits) if total_credits.is_integer() else total_credits} 単位")
st.caption("※ 時間割から科目を選択すると、全学期を合算した単位数がリアルタイムで集計されます。")

st.markdown("---")

# 時間割の構築
st.subheader("📅 時間割表")

days = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日"]
periods = [1, 2, 3, 4, 5]

# 曜日ヘッダー
cols = st.columns([0.8] + [2]*5)
cols[0].write("**時限**")
for idx, day in enumerate(days):
    cols[idx + 1].markdown(f"<div class='period-header'>{day}</div>", unsafe_allow_html=True)

# 各時限の選択UI
for period in periods:
    cols = st.columns([0.8] + [2]*5)
    cols[0].write(f"**{period}限**")
    
    for idx, day in enumerate(days):
        col = cols[idx + 1]
        
        # 該当する曜日・時限の科目を抽出
        slot_courses = filtered_df[
            (filtered_df["曜日"].astype(str).str.contains(day[:1])) & 
            (filtered_df["時限"].astype(str).str.contains(str(period)))
        ]
        
        options = ["-- 未選択 --"] + slot_courses["科目名"].tolist()
        
        # 前期選択
        col.markdown("<div class='sub-label'>【前期】</div>", unsafe_allow_html=True)
        key_zen = f"{target_year}_{day}_{period}_前期"
        col.selectbox(
            "【前期】",
            options,
            key=key_zen,
            label_visibility="collapsed"
        )
        
        # 後期選択
        col.markdown("<div class='sub-label'>【後期】</div>", unsafe_allow_html=True)
        key_kou = f"{target_year}_{day}_{period}_後期"
        col.selectbox(
            "【後期】",
            options,
            key=key_kou,
            label_visibility="collapsed"
        )

if selected_summary:
    st.markdown("---")
    st.write("#### 選択中科目一覧")
    st.dataframe(pd.DataFrame(selected_summary), use_container_width=True)
