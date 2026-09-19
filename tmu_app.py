import streamlit as st
import pandas as pd

# ページの設定（ワイドモード）
st.set_page_config(page_title="都立大 情報科学 時間割・単位計算ツール", layout="wide")

# スマホ表示時でも st.columns の横並び（カラム）を維持するカスタムCSS
st.markdown("""
<style>
/* Streamlitのカラム要素（st.columns）がスマホで縦落ちするのを防止 */
[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    overflow-x: auto;
}

/* カラムごとの最小幅・隙間調整 */
[data-testid="column"] {
    min-width: 0px !important;
    padding: 0 2px !important;
}

/* セレクトボックスや文字サイズをスマホ向けにコンパクト化 */
div[data-baseweb="select"] {
    font-size: 12px !important;
}

label {
    font-size: 12px !important;
}
</style>
""", unsafe_allow_html=True)

st.title("📚 シラバス・時間割作成ツール")

# シラバスデータの読み込み
@st.cache_data
def load_data():
    df = pd.read_csv("syllabus_tmu.csv")
    return df

try:
    df = load_data()
except Exception as e:
    st.error("syllabus_tmu.csv の読み込みに失敗しました。ファイルがリポジトリ内に存在するか確認してください。")
    st.stop()

# 対象学年フィルター
st.write("### 表示・選択する対象学年を選んでください")
target_year = st.radio("学年", ["1年", "2年", "3年", "4年"], horizontal=True)

# 学年フィルタリング
year_num = int(target_year.replace("1年", "1").replace("2年", "2").replace("3年", "3").replace("4年", "4"))
filtered_df = df[df["学年"] == year_num]

st.markdown("---")

# 曜日と時限の設定
days = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日"]
periods = [1, 2, 3, 4, 5]

# 選択科目を保持するセッション状態の初期化
if "selected_courses" not in st.session_state:
    st.session_state["selected_courses"] = {}

# 時間割の構築
st.subheader("📅 時間割表")

# 曜日ヘッダー
cols = st.columns([1] + [2]*5)
cols[0].write("**時限**")
for idx, day in enumerate(days):
    cols[idx + 1].write(f"**{day[:1]}曜**")

# 各時限の選択UI
for period in periods:
    cols = st.columns([1] + [2]*5)
    cols[0].write(f"**{period}限**")
    
    for idx, day in enumerate(days):
        col = cols[idx + 1]
        
        # 該当する曜日・時限の科目を抽出
        slot_courses = filtered_df[
            (filtered_df["曜日"] == day) & 
            (filtered_df["時限"] == period)
        ]
        
        options = ["-- 未選択 --"] + slot_courses["科目名"].tolist()
        
        # 前期
        key_zen = f"{target_year}_{day}_{period}_前期"
        selected_zen = col.selectbox(
            f"【前期】",
            options,
            key=key_zen,
            label_visibility="collapsed"
        )
        
        # 後期
        key_kou = f"{target_year}_{day}_{period}_後期"
        selected_kou = col.selectbox(
            f"【後期】",
            options,
            key=key_kou,
            label_visibility="collapsed"
        )

st.markdown("---")

# 単位数の集計
st.subheader("📊 年間取得単位数（全学期・全区分 合算）")

total_credits = 0
selected_summary = []

for key, course_name in st.session_state.items():
    if course_name != "-- 未選択 --" and isinstance(course_name, str):
        match_row = df[df["科目名"] == course_name]
        if not match_row.empty:
            credit = match_row.iloc[0]["単位数"]
            total_credits += credit
            selected_summary.append({
                "科目名": course_name,
                "単位数": credit,
                "区分": match_row.iloc[0]["区分"]
            })

st.metric("合計取得単位数", f"{total_credits} 単位")

if selected_summary:
    st.write("#### 選択中科目一覧")
    st.dataframe(pd.DataFrame(selected_summary), use_container_width=True)
