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

# シラバスデータの読み込みと列名の表記揺れ吸収
@st.cache_data
def load_data():
    df = pd.read_csv("syllabus_tmu.csv")
    
    # 列名の表記揺れを補正するマッピング
    column_mapping = {
        '対象学年': '学年',
        '単位': '単位数',
        '開講期': '学期',
        '履修区分': '区分'
    }
    df = df.rename(columns=column_mapping)
    
    # 学年列を数値型にキャスト（"1年" や 1 どちらにも対応）
    if '学年' in df.columns:
        df['学年'] = df['学年'].astype(str).str.extract(r'(\d+)').astype(int)
        
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"syllabus_tmu.csv の読み込みまたはデータ形式に問題があります: {e}")
    st.stop()

# 必要な列の存在チェック
required_cols = ['学年', '曜日', '時限', '科目名', '単位数']
missing_cols = [c for c in required_cols if c not in df.columns]
if missing_cols:
    st.error(f"CSVファイルに必要な列が存在しません: { missing_cols }")
    st.info(f"現在のCSVの列名: {list(df.columns)}")
    st.stop()

# 対象学年フィルター
st.write("### 表示・選択する対象学年を選んでください")
target_year = st.radio("学年", ["1年", "2年", "3年", "4年"], horizontal=True)

year_num = int(target_year.replace("1年", "1").replace("2年", "2").replace("3年", "3").replace("4年", "4"))
filtered_df = df[df["学年"] == year_num]

st.markdown("---")

# 曜日と時限の設定
days = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日"]
periods = [1, 2, 3, 4, 5]

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
            (filtered_df["曜日"].str.contains(day[:1])) & 
            (filtered_df["時限"].astype(str).str.contains(str(period)))
        ]
        
        options = ["-- 未選択 --"] + slot_courses["科目名"].tolist()
        
        # 前期
        key_zen = f"{target_year}_{day}_{period}_前期"
        col.selectbox(
            f"【前期】",
            options,
            key=key_zen,
            label_visibility="collapsed"
        )
        
        # 後期
        key_kou = f"{target_year}_{day}_{period}_後期"
        col.selectbox(
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
    if isinstance(course_name, str) and course_name != "-- 未選択 --":
        match_row = df[df["科目名"] == course_name]
        if not match_row.empty:
            credit = float(match_row.iloc[0]["単位数"])
            total_credits += credit
            cat = match_row.iloc[0]["区分"] if "区分" in match_row.columns else "-"
            selected_summary.append({
                "科目名": course_name,
                "単位数": credit,
                "区分": cat
            })

st.metric("合計取得単位数", f"{int(total_credits) if total_credits.is_integer() else total_credits} 単位")

if selected_summary:
    st.write("#### 選択中科目一覧")
    st.dataframe(pd.DataFrame(selected_summary), use_container_width=True)