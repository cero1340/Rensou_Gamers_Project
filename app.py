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

# フォント設定（筆文字）
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
# 3. 初期化処理
# ==========================================
st.title("🔒 連想 Gamers Training App")
password = st.text_input("メンバー限定パスワード", type="password")

if password != st.secrets.get("SECRET_PASSWORD", "2025"):
    st.info("パスワードを入力してください。(テスト用: 2025)")
    st.stop()

data = load_json(JSON_FILE)
template = load_json(TEMPLATE_FILE)

if not data or not template:
    st.error("データファイルが見つかりません。")
    st.stop()

# セッションステート初期化（チャットログ用）
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [] 

# ==========================================
# 4. ゲーム進行エリア
# ==========================================

# --- カテゴリ選択エリア ---
# 日本語のキー（"1_場所"など）をリスト化
step_list = list(template.keys())
current_step_label = st.selectbox("カテゴリを選択 (Step)", step_list)

# 選ばれたカテゴリのデータ取得
step_data = template[current_step_label]
question_prefix = step_data["question"] # "Can you find it..."
options_dict = step_data["options"]     # 選択肢リスト

# ★ここが重要：Qの横にキーフレーズを表示
st.subheader(f"Q: {question_prefix} ... ?")

# --- 入力フォーム ---
with st.form(key='game_form', clear_on_submit=True):
    
    # 音声/テキスト入力
    user_input = st.text_input(
        "🎤 A. 自分で聞く (Voice/Text)", 
        placeholder=f"例: {question_prefix} house?"
    )

    # リストから選ぶ (現在は全表示テスト)
    # JSON構造変更に対応: options_dictの値は {"keyword": "...", "level": 1}
    # 表示用には日本語キーを使う
    option_labels = ["(リストから選択)"] + list(options_dict.keys())
    selected_option_label = st.selectbox("📝 B. リストから選ぶ (Hint)", option_labels)
    
    submit_button = st.form_submit_button(label='送信 (Submit)')

# ==========================================
# 5. 判定ロジック
# ==========================================
if submit_button:
    search_keyword = None
    display_question = ""

    # A. 自分で入力
    if user_input:
        input_text = user_input.lower()
        display_question = user_input # そのまま表示
        
        # 全カテゴリから検索
        found = False
        for s_content in template.values():
            for label, val_obj in s_content["options"].items():
                # val_objは {"keyword": "...", "level": 1}
                kw = val_obj["keyword"]
                if kw in input_text or label in input_text:
                    search_keyword = kw
                    found = True
                    break
            if found: break
        
        if not search_keyword:
            # 見つからなくてもチャットには残す
            st.session_state.chat_history.append({
                "role": "user", "content": user_input
            })
            st.session_state.chat_history.append({
                "role": "assistant", "content": "🤔 うまく聞き取れませんでした。", "status": "warning"
            })

    # B. リストから選択
    elif selected_option_label != "(リストから選択)":
        # 選択肢データからキーワードを取り出す
        val_obj = options_dict[selected_option_label]
        search_keyword = val_obj["keyword"]
        
        # 質問文を組み立てて表示用に
        display_question = f"{question_prefix} {search_keyword}?"

    # --- 回答検索とログ保存 ---
    if search_keyword:
        # ユーザーの質問を履歴に追加
        st.session_state.chat_history.append({
            "role": "user", "content": display_question
        })

        # 答えを探す
        all_rules = {}
        for cat in data["rules"].values():
            all_rules.update(cat)
        
        if search_keyword in all_rules:
            answer_key = all_rules[search_keyword]
            display_answer = data["response_map"].get(answer_key, answer_key).replace(".wav", "").upper()
            
            status = "success" if ("YES" in display_answer or "CORRECT" in display_answer) else "error"
            
            # AIの回答を履歴に追加
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": f"AI: **{display_answer}**", 
                "status": status
            })
            if status == "success": st.balloons()
            
        else:
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": f"データなし: {search_keyword}", 
                "status": "warning"
            })

# ==========================================
# 6. チャット履歴表示 (ここが新しいUI)
# ==========================================
st.divider()
st.caption("📝 Chat History")

# 履歴が空の場合
if not st.session_state.chat_history:
    st.info("質問すると、ここにチャット形式で履歴が残ります。")

# 履歴ループ表示（新しいものが下）
for chat in st.session_state.chat_history:
    
    # ユーザーのターン
    if chat["role"] == "user":
        with st.chat_message("user", avatar="😊"):
            st.write(chat["content"])
            
    # AIのターン
    elif chat["role"] == "assistant":
        with st.chat_message("assistant", avatar="🤖"):
            # ステータスによって色を変える
            if chat.get("status") == "success":
                st.success(chat["content"])
            elif chat.get("status") == "error":
                st.error(chat["content"])
            else:
                st.warning(chat["content"])