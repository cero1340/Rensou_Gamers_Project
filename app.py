import streamlit as st
import json
import os

# ==========================================
# 1. 設定エリア
# ==========================================
SECRET_PASSWORD = "2025"
JSON_FILE = "microwave_data.json"
TEMPLATE_FILE = "Questions_template.json" 

st.set_page_config(page_title="連想 Training", page_icon="🎮")

# フォント設定
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Yuji+Syuku&display=swap');
h1 { font-family: 'Yuji Syuku', serif !important; font-weight: 400; }
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
# 3. 初期化 & データ読み込み
# ==========================================
st.title("🔒 連想 Gamers Training App")

# パスワード認証
password = st.text_input("Password", type="password")
if password != st.secrets.get("SECRET_PASSWORD", "2025"):
    st.stop()

data = load_json(JSON_FILE)
template = load_json(TEMPLATE_FILE)

if not data or not template:
    st.error("データファイルが見つかりません。")
    st.stop()

# セッションステート初期化
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [] 

# ==========================================
# 4. チャット履歴の表示 (ここを上に配置)
# ==========================================
# LINEのように、古い順(上) -> 新しい順(下) に表示
for chat in st.session_state.chat_history:
    if chat["role"] == "user":
        with st.chat_message("user", avatar="😊"):
            st.write(chat["content"])
    elif chat["role"] == "assistant":
        with st.chat_message("assistant", avatar="🤖"):
            if chat.get("status") == "success":
                st.success(chat["content"])
            elif chat.get("status") == "error":
                st.error(chat["content"])
            else:
                st.warning(chat["content"])

st.divider() # 履歴と入力欄の区切り線

# ==========================================
# 5. 入力エリア (ここを下に配置)
# ==========================================

# --- カテゴリ選択 (プルダウン) ---
step_list = list(template.keys())
# カテゴリ名はJSONのキーそのまま(日本語)を使用
current_step_label = st.selectbox("Category Select", step_list)

# 選ばれたカテゴリのデータ
step_data = template[current_step_label]
question_prefix = step_data["question"]
options_dict = step_data["options"]

# Q: ... の表示
st.markdown(f"### Q: {question_prefix} ... ?")

# --- 入力フォーム ---
with st.form(key='game_form', clear_on_submit=True):
    
    # 1. 自分で入力 (音声/テキスト)
    user_input = st.text_input(
        "🎤 Voice / Text Input", 
        placeholder=f"Ex: {question_prefix} house?"
    )

    # 2. リストから選ぶ (英語リスト)
    # 選択肢ラベル(英語)をリスト化
    option_labels = ["(Select from list)"] + list(options_dict.keys())
    selected_option_label = st.selectbox("📝 Hint List", option_labels)
    
    # 送信ボタン
    submit_button = st.form_submit_button(label='Submit (送信)')

# ==========================================
# 6. 判定ロジック (送信後の処理)
# ==========================================
if submit_button:
    search_keyword = None
    display_question = ""

    # A. 自分で入力した場合
    if user_input:
        input_text = user_input.lower()
        display_question = user_input
        
        # 全カテゴリ検索
        found = False
        for s_content in template.values():
            for label, val_obj in s_content["options"].items():
                # label(英語) または keyword で検索
                kw = val_obj["keyword"]
                if kw in input_text or label.lower() in input_text:
                    search_keyword = kw
                    found = True
                    break
            if found: break
        
        if not search_keyword:
            # マッチしなくても履歴に残す
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            st.session_state.chat_history.append({"role": "assistant", "content": "🤔 Sorry, I didn't catch that.", "status": "warning"})
            st.rerun() # 即再描画

    # B. リストから選んだ場合
    elif selected_option_label != "(Select from list)":
        val_obj = options_dict[selected_option_label]
        search_keyword = val_obj["keyword"]
        display_question = f"{question_prefix} {selected_option_label}?"

    # --- 判定処理 ---
    if search_keyword:
        # ユーザー発言を履歴へ
        st.session_state.chat_history.append({
            "role": "user", "content": display_question
        })

        # 回答検索
        all_rules = {}
        for cat in data["rules"].values():
            all_rules.update(cat)
        
        if search_keyword in all_rules:
            answer_key = all_rules[search_keyword]
            # .wav拡張子を削除して大文字に
            display_answer = data["response_map"].get(answer_key, answer_key).replace(".wav", "").upper()
            
            status = "success" if ("YES" in display_answer or "CORRECT" in display_answer) else "error"
            
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": f"AI: **{display_answer}**", 
                "status": status
            })
        else:
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": f"Data not found: {search_keyword}", 
                "status": "warning"
            })
        
        st.rerun() # 画面を更新して最新のチャットを表示