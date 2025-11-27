import streamlit as st
import json
import os

# ==========================================
# 1. 設定エリア
# ==========================================

JSON_FILE = "microwave_data.json"
# クラウド上のファイル名(大文字Q)に合わせる
TEMPLATE_FILE = "Questions_template.json" 

# ブラウザのタブ名設定
st.set_page_config(page_title="連想 Training", page_icon="🎮")

# ★デザイン変更：タイトルを筆文字（Yuji Syuku）にする設定
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Yuji+Syuku&display=swap');

/* タイトル(h1)を筆文字にする */
h1 {
    font-family: 'Yuji Syuku', serif !important;
    font-weight: 400;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 関数定義
# ==========================================
def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading {filename}: {e}")
            return None
    return None

# ==========================================
# 3. メイン処理開始 (初期化)
# ==========================================

# タイトル（筆文字になります）
st.title("🔒 連想 Gamers Training App")
password = st.text_input("メンバー限定パスワード", type="password")

if password != st.secrets["SECRET_PASSWORD"]:
    st.info("パスワードを入力してください。(テスト用: 2025)")
    st.stop()

# データ読み込み
data = load_json(JSON_FILE)
template = load_json(TEMPLATE_FILE)

if not data or not template:
    st.error("データファイルが見つかりません。")
    st.stop()

# ネタバレ防止メッセージ
st.success("Login OK! Game Start! 🎮")
st.divider()

if "clue_log" not in st.session_state:
    st.session_state.clue_log = []
# ★追加：前回の回答を保存するためのステート
if "last_answer_status" not in st.session_state:
    st.session_state.last_answer_status = None
if "last_answer_text" not in st.session_state:
    st.session_state.last_answer_text = None

# ==========================================
# 4. ゲーム進行エリア
# ==========================================

# ★追加：使い方ガイド（アコーディオン形式）
with st.expander("❓ アプリの使い方 (How to Play)"):
    st.markdown("""
        **1. ログイン:** パスワード (**2025**) を入力してアプリに入ります。
        **2. 質問 (Input):**
           - 上のテキスト欄をタップし、スマホの**英語キーボード**で発話/入力してください。
           - ヒント: 入力欄の例文やリスト（B）を参考に質問を組み立ててください。
        **3. ログ (Clue Log):** AIが「YES」と答えた質問は自動で下に記録されます。
        **4. 判定:** 文章を入力したら「送信 (Submit)」を押すと、AIが回答を返します。
        **5. ギブアップ:** 一番下の「答えを見る」を開くと、いつでも正解が確認できます。
        """)

# 音声入力の注意書き
st.warning("⚠️ 音声入力でやる場合は、スマホを「英語キーボード」に切り替えてからマイクボタンを押してください。")

# ステップ選択（カンペ用）
step_list = list(template.keys())
current_step = st.selectbox("ステップを選択（カンペ用）", step_list)

# 選ばれたステップの情報を取得
step_data = template[current_step]
question_prefix = step_data["question"]
options_dict = step_data["options"]

# 自動で例文を作る機能
first_option_key = list(options_dict.keys())[0] 
example_sentence = f"例: {question_prefix} {first_option_key}?"

st.subheader(f"Q: {question_prefix} ... ?")

# ★修正ポイント：前回の回答結果を質問のすぐ下に表示
if st.session_state.last_answer_text:
    if st.session_state.last_answer_status == 'success':
        st.success(st.session_state.last_answer_text)
    elif st.session_state.last_answer_status == 'error':
        st.error(st.session_state.last_answer_text)
    elif st.session_state.last_answer_status == 'warning':
        st.warning(st.session_state.last_answer_text)

# フォーム作成 (回答の下にフォームが配置される)
with st.form(key='game_form', clear_on_submit=True):
    
    # 1. 音声/テキスト入力欄 (placeholderに例文を入れる)
    user_input = st.text_input(
        "🎤 A. 自分で聞く (音声/テキスト)", 
        placeholder=example_sentence
    )

    # 2. 選択肢（カンペ）
    selected_option_label = st.selectbox(
        "📝 B. リストから選ぶ", 
        ["(選択してください)"] + list(options_dict.keys())
    )
    
    # 送信ボタン
    submit_button = st.form_submit_button(label='送信 (Submit)')


# ==========================================
# 5. 判定ロジック
# ==========================================
if submit_button:
    search_keyword = None
    matched_step = current_step

    # --- Aパターン: 自分で入力した場合 ---
    if user_input:
        input_text = user_input.lower()
        
        # 全ステップのテンプレートから検索する
        found = False
        for step_name, step_content in template.items():
            for label, keyword in step_content["options"].items():
                if keyword in input_text or label in input_text:
                    search_keyword = keyword
                    matched_step = step_name
                    found = True
                    break
            if found:
                break
        
        if not search_keyword:
            # 修正：直接表示せず、ステートに保存
            st.session_state.last_answer_status = 'warning'
            st.session_state.last_answer_text = "🤔 うまく聞き取れませんでした。別の言い方を試してみて！"

    # --- Bパターン: リストから選んだ場合 ---
    elif selected_option_label != "(選択してください)":
        search_keyword = options_dict[selected_option_label]
        
    # --- 結果表示（ステートに保存） ---
    if search_keyword:
        # ルール検索
        all_rules = {}
        for cat in data["rules"].values():
            all_rules.update(cat)
        
        if search_keyword in all_rules:
            answer_key = all_rules[search_keyword]
            display_answer = data["response_map"].get(answer_key, answer_key).replace(".wav", "").upper()
            
            if "YES" in display_answer or "CORRECT" in display_answer:
                # 修正：直接表示せず、ステートに保存
                st.session_state.last_answer_status = 'success'
                st.session_state.last_answer_text = f"🤖 AI: **{display_answer}**"
                st.balloons()
                
                # ログ保存
                log_entry = f"{matched_step}: {search_keyword} ({display_answer})"
                if log_entry not in st.session_state.clue_log:
                    st.session_state.clue_log.append(log_entry)
            else:
                # 修正：直接表示せず、ステートに保存
                st.session_state.last_answer_status = 'error'
                st.session_state.last_answer_text = f"🤖 AI: **{display_answer}**"
        else:
            # 修正：直接表示せず、ステートに保存
            st.session_state.last_answer_status = 'warning'
            st.session_state.last_answer_text = f"🤔 データなし: {search_keyword}"

# ==========================================
# 6. 情報表示エリア
# ==========================================
st.divider()
st.write("📝 **Clue Log (わかったことメモ)**")
if st.session_state.clue_log:
    for log in st.session_state.clue_log:
        st.info(log)
else:
    st.caption("ヒントはここに溜まります。")

with st.expander("答えを見る（ギブアップ）"):
    st.write(f"正解は... **{data['item_name']} ({data['item_name_en']})** でした！")