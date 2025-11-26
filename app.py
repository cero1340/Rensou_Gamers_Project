import streamlit as st
import json
import os

# ==========================================
# 1. 設定エリア
# ==========================================
SECRET_PASSWORD = "2025"
JSON_FILE = "microwave_data.json"
# クラウド上のファイル名(大文字Q)に合わせる
TEMPLATE_FILE = "Questions_template.json" 

# ブラウザのタブ名も「連想」に変更
st.set_page_config(page_title="連想 Training", page_icon="🎮")

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

# ★修正ポイント：タイトルを日本語化
st.title("🔒 連想 Gamers Training App")
password = st.text_input("メンバー限定パスワード", type="password")

if password != SECRET_PASSWORD:
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

# ==========================================
# 4. ゲーム進行エリア
# ==========================================

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
first_option_key = list(options_dict.keys())[0] # 例: "in the house"
example_sentence = f"例: {question_prefix} {first_option_key}?"

st.subheader(f"Q: {question_prefix} ... ?")

# フォーム作成 (clear_on_submit=True で送信後に消える)
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
    matched_step = current_step # どのステップでヒットしたか記録用

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
            st.warning("🤔 うまく聞き取れませんでした。別の言い方を試してみて！")

    # --- Bパターン: リストから選んだ場合 ---
    elif selected_option_label != "(選択してください)":
        search_keyword = options_dict[selected_option_label]

    # --- 結果表示 ---
    if search_keyword:
        # ルール検索
        all_rules = {}
        for cat in data["rules"].values():
            all_rules.update(cat)
        
        if search_keyword in all_rules:
            answer_key = all_rules[search_keyword]
            display_answer = data["response_map"].get(answer_key, answer_key).replace(".wav", "").upper()
            
            if "YES" in display_answer or "CORRECT" in display_answer:
                st.success(f"🤖 AI: **{display_answer}**")
                st.balloons()
                
                # ログ保存
                log_entry = f"{matched_step}: {search_keyword} ({display_answer})"
                if log_entry not in st.session_state.clue_log:
                    st.session_state.clue_log.append(log_entry)
            else:
                st.error(f"🤖 AI: **{display_answer}**")
        else:
            st.warning(f"🤔 データなし: {search_keyword}")

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