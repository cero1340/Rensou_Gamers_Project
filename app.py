import streamlit as st
import json
import os
import time
import re

# ==========================================
# 1. 設定エリア
# ==========================================
JSON_FILE = "microwave_data.json"
TEMPLATE_FILE = "Questions_template.json"
TRAINING_FILE = "training_data.json"

st.set_page_config(page_title="連想 Training", page_icon="🎮")

# ==========================================
# ★ CSS定義 (モード共通 + 各モード専用) ★
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Yuji+Syuku&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Helvetica Neue', 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', Arial, sans-serif;
    }
    h1 { font-family: 'Yuji Syuku', serif !important; font-weight: 400; }
    
    /* 全体背景 */
    .stApp {
        background-color: #7494c0;
    }

    /* --- 上級者モード用 (LINE風) --- */
    .chat-scroll-area {
        height: 500px;
        overflow-y: auto;
        display: flex;
        flex-direction: column-reverse;
        padding: 20px;
        background-color: rgba(255, 255, 255, 0.1); 
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .user-bubble {
        background-color: #98e165;
        color: black;
        padding: 10px 15px;
        border-radius: 15px;
        border-top-right-radius: 0;
        margin: 5px 0 5px auto;
        max-width: 80%;
        width: fit-content;
        box-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        text-align: left;
        line-height: 1.5;
    }
    .bot-bubble-container {
        display: flex;
        align-items: flex-start;
        margin: 5px 0;
    }
    .bot-avatar {
        font-size: 24px;
        margin-right: 8px;
    }
    .bot-bubble {
        background-color: #ffffff;
        color: black;
        padding: 10px 15px;
        border-radius: 15px;
        border-top-left-radius: 0;
        max-width: 80%;
        box-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        text-align: left;
        line-height: 1.5;
    }

    /* --- 初級者モード用 (ドリル風) --- */
    .question-box {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .question-label {
        font-size: 16px;
        color: #555;
        margin-bottom: 10px;
    }
    .question-text {
        font-size: 40px;      /* 巨大文字 */
        font-weight: bold;
        color: #333;          /* 白背景なので黒文字 */
        line-height: 1.2;
    }
    .feedback-msg {
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        margin-top: 10px;
        padding: 10px;
        border-radius: 5px;
    }
    .feedback-good { color: #2e7d32; background-color: #e8f5e9; } /* 緑 */
    .feedback-retry { color: #d32f2f; background-color: #ffebee; } /* 赤 */
    .feedback-next { color: #1976d2; background-color: #e3f2fd; } /* 青 */

    /* 入力フォーム共通 */
    [data-testid="stForm"] {
        background-color: rgba(255, 255, 255, 0.95);
        padding: 15px;
        border-radius: 10px;
    }

    /* サイドバーMenuボタン化 */
    button[data-testid="stSidebarCollapsedControl"] {
        width: auto !important; height: auto !important;
        padding: 8px 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.8) !important;
        border-radius: 8px !important;
        background-color: rgba(255, 255, 255, 0.2) !important;
        color: white !important;
    }
    button[data-testid="stSidebarCollapsedControl"] > svg { display: none !important; }
    button[data-testid="stSidebarCollapsedControl"]::after {
        content: "Menu" !important;
        font-family: Arial, sans-serif !important;
        font-weight: bold !important;
        font-size: 16px !important;
        line-height: 1 !important;
    }

</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 関数・データ読み込み
# ==========================================
def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return None
    return None

def normalize_text(text):
    if not text: return ""
    text = re.sub(r'[.?,]+', ' ', text)
    return " ".join(text.split()).lower()

# データロード
data = load_json(JSON_FILE)
template = load_json(TEMPLATE_FILE)
training_data = load_json(TRAINING_FILE)

if not data or not template or not training_data:
    st.error("データファイル不足")
    st.stop()

# ==========================================
# 3. セッションステート初期化
# ==========================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [] 

# 初級者モード用ステート
if "training_cat_index" not in st.session_state:
    st.session_state.training_cat_index = 0 # 現在の質問番号
if "mistake_count" not in st.session_state:
    st.session_state.mistake_count = 0 # 失敗回数
if "last_feedback" not in st.session_state:
    st.session_state.last_feedback = "" # 直前の判定結果
if "completed_phrases" not in st.session_state:
    st.session_state.completed_phrases = set() # クリア済みリスト
if "current_category" not in st.session_state:
    st.session_state.current_category = "1. 場所 (Place)" # 初期カテゴリ

# ==========================================
# 4. サイドバー (モード切替)
# ==========================================
with st.sidebar:
    st.title("Settings")
    mode = st.radio("Mode Select:", ["🔰 初級者 (Training)", "🔥 上級者 (Advanced)"])
    
    st.markdown("---")
    if st.button("Reset All"):
        st.session_state.chat_history = []
        st.session_state.completed_phrases = set()
        st.session_state.training_cat_index = 0
        st.session_state.mistake_count = 0
        st.session_state.last_feedback = ""
        st.rerun()

st.title("🔒 連想 Gamers Training App")

# パスワード認証
if os.environ.get("STREAMLIT_ENV") == "CLOUD":
    SECRET_PASSWORD_VAL = st.secrets.get("SECRET_PASSWORD", "2025")
else:
    SECRET_PASSWORD_VAL = "2025"
password = st.text_input("Password", type="password")
if password != SECRET_PASSWORD_VAL:
    st.stop()

# ==========================================
# 5. メイン画面 (モード分岐)
# ==========================================

# ---------------------------------------------------------
# 【A】初級者モード (ドリル形式 UI)
# ---------------------------------------------------------
if mode == "🔰 初級者 (Training)":
    
    # 1. カテゴリ選択
    categories = sorted(list(set(item["category"] for item in training_data)))
    selected_cat = st.selectbox("カテゴリー選択", categories)
    
    # カテゴリが変わったらリセットする処理
    if selected_cat != st.session_state.current_category:
        st.session_state.current_category = selected_cat
        st.session_state.training_cat_index = 0
        st.session_state.mistake_count = 0
        st.session_state.last_feedback = ""
        st.rerun()

    # 現在のカテゴリのタスクだけを抽出
    current_tasks = [t for t in training_data if t["category"] == selected_cat]
    
    # 2. Qの表示エリア
    if st.session_state.training_cat_index < len(current_tasks):
        target_task = current_tasks[st.session_state.training_cat_index]
        q_text = target_task["question"]
        
        # 白い箱にQを表示
        st.markdown(f"""
        <div class="question-box">
            <div class="question-label">Q: Read this aloud!</div>
            <div class="question-text">{q_text}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # フィードバック表示
        fb = st.session_state.last_feedback
        if fb == "Good!":
            st.markdown('<div class="feedback-msg feedback-good">Good! 👍</div>', unsafe_allow_html=True)
        elif fb == "Retry":
            st.markdown('<div class="feedback-msg feedback-retry">もう一回！ (Try again) 💦</div>', unsafe_allow_html=True)
        elif fb == "Almost":
            st.markdown('<div class="feedback-msg feedback-retry">もうちょいだ！ (Almost) 🔥</div>', unsafe_allow_html=True)
        elif fb == "Skip":
            st.markdown('<div class="feedback-msg feedback-next">よし！次いこう！ (Next) 🚀</div>', unsafe_allow_html=True)

    else:
        # カテゴリコンプリート時
        st.markdown("""
        <div class="question-box">
            <div class="question-text">🎉 Category Complete! 🎉</div>
        </div>
        """, unsafe_allow_html=True)
        target_task = None
        
        # ★追加: このカテゴリーだけリセットするボタン★
        if st.button("Retry this Category"):
            # 現在のカテゴリ内のキーワードをクリア済みセットから削除
            for t in current_tasks:
                kw = t.get("keyword")
                if kw in st.session_state.completed_phrases:
                    st.session_state.completed_phrases.remove(kw)
            
            # インデックス等をリセット
            st.session_state.training_cat_index = 0
            st.session_state.mistake_count = 0
            st.session_state.last_feedback = ""
            st.rerun()

    # 3. 入力フォーム
    if target_task:
        with st.form(key='training_form', clear_on_submit=True):
            user_input = st.text_input("Voice/Text: 入力する", placeholder="上の英文を読んでください")
            submit_button = st.form_submit_button(label='送信する')

        if submit_button and user_input:
            clean_input = normalize_text(user_input)
            t_kw = target_task.get("keyword", "")
            t_q = target_task.get("question", "")
            
            # 正解判定
            if t_kw in clean_input or normalize_text(t_q) in clean_input:
                st.session_state.last_feedback = "Good!"
                st.session_state.completed_phrases.add(t_kw)
                st.session_state.training_cat_index += 1
                st.session_state.mistake_count = 0
            else:
                st.session_state.mistake_count += 1
                count = st.session_state.mistake_count
                
                if count == 1:
                    st.session_state.last_feedback = "Retry"
                elif count == 2:
                    st.session_state.last_feedback = "Almost"
                elif count >= 3:
                    st.session_state.last_feedback = "Skip"
                    st.session_state.training_cat_index += 1
                    st.session_state.mistake_count = 0
            
            st.rerun()

    # 4. リスト表示 (達成状況)
    st.markdown("---")
    st.markdown("**List Progress:**")
    for t in current_tasks:
        kw = t["keyword"]
        q = t["question"]
        if kw in st.session_state.completed_phrases:
            st.markdown(f"✅ **{q}**")
        else:
            if t == target_task:
                st.markdown(f"👉 **{q}**")
            else:
                st.markdown(f"⬜ {q}")


# ---------------------------------------------------------
# 【B】上級者モード (LINE風チャット UI - ヒントなし)
# ---------------------------------------------------------
else: # mode == "🔥 上級者 (Advanced)"
    
    st.header("💬 チャットゲーム開始！")
    
    # 1. チャット履歴 (LINE風)
    chat_html = '<div class="chat-scroll-area">'
    for chat in reversed(st.session_state.chat_history):
        if chat["role"] == "user":
            chat_html += f'<div class="user-bubble">{chat["content"]}</div>'
        elif chat["role"] == "assistant":
            content = chat["content"]
            status = chat.get("status")
            display_text = f"🟢 {content}" if status == "success" else (f"🔴 {content}" if status == "error" else f"🟡 {content}")
            chat_html += f'<div class="bot-bubble-container"><div class="bot-avatar">🤖</div><div class="bot-bubble">{display_text}</div></div>'
    chat_html += '</div>'
    st.markdown(chat_html, unsafe_allow_html=True)

    # 2. 入力フォーム (シンプル版)
    with st.form(key='gamer_form', clear_on_submit=True):
        user_input = st.text_input("Voice/Text: 質問を入力 (ヒントなし)", placeholder="Ex: Is it made of metal?")
        submit_button = st.form_submit_button(label='送信する')

    if submit_button and user_input:
        clean_input = normalize_text(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # 判定ロジック (JSONから検索)
        search_keyword = None
        all_candidates = []
        for s_content in template.values():
            for label, val_obj in s_content["options"].items():
                all_candidates.append((label, val_obj["keyword"]))
        all_candidates.sort(key=lambda x: len(x[0]), reverse=True)
        
        for label, kw in all_candidates:
            if normalize_text(label) in clean_input or kw in clean_input:
                search_keyword = kw
                break
        
        if search_keyword:
            # 回答検索
            all_rules = {}
            for cat in data["rules"].values():
                all_rules.update(cat)
            
            if search_keyword in all_rules:
                answer_key = all_rules[search_keyword]
                raw_answer = data["response_map"].get(answer_key, answer_key).replace(".wav", "").upper()
                
                # 表示用日本語変換
                display_map = {
                    "YES": "イエス！", "NO": "ノー！", "PARTIAL_YES": "部分的にはイエス！",
                    "CORRECT": "正解！", "USUALLY_YES": "通常はイエスかな！",
                    "DEPENS": "状況によるよ！", "SOME_PEOPLE_USE": "使う人もいるよ！"
                }
                display_answer = display_map.get(raw_answer, raw_answer)
                is_positive = any(k in raw_answer for k in ["YES", "CORRECT", "PARTIAL"])
                status = "success" if is_positive else "error"
                
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": f"AI: <b>{display_answer}</b>", 
                    "status": status
                })
            else:
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": f"Data not found: {search_keyword}", 
                    "status": "warning"
                })
        else:
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": "🤔 Sorry, I didn't catch that.", 
                "status": "warning"
            })
        
        st.rerun()