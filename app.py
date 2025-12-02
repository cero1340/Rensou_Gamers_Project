import streamlit as st
import json
import os
import re

# ==========================================
# 1. 設定エリア (ここを修正！)
# ==========================================
# app.py があるフォルダの場所を特定する
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# その場所を基準にしてファイル名を指定する (これで迷子にならない)
JSON_FILE = os.path.join(BASE_DIR, "microwave_data.json")
TEMPLATE_FILE = os.path.join(BASE_DIR, "Questions_template.json")
TRAINING_FILE = os.path.join(BASE_DIR, "training_data.json")

st.set_page_config(page_title="連想 Training", page_icon="🎮")

# ★これを追加して、画面にファイル一覧を表示させる！
# st.write("📂 フォルダの中身:", os.listdir(BASE_DIR))

# ==========================================
# ★ CSS定義
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Yuji+Syuku&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Helvetica Neue', 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', Arial, sans-serif;
    }
    h1 { font-family: 'Yuji Syuku', serif !important; font-weight: 400; }
    
    .stApp { background-color: #7494c0; }

    /* 上級者モード (LINE風) */
    .chat-scroll-area {
        height: 400px; overflow-y: auto; display: flex; flex-direction: column-reverse;
        padding: 20px; background-color: rgba(255, 255, 255, 0.1); 
        border-radius: 10px; margin-bottom: 10px;
    }
    .user-bubble {
        background-color: #98e165; color: black; padding: 10px 15px;
        border-radius: 15px; border-top-right-radius: 0;
        margin: 5px 0 5px auto; max-width: 80%; width: fit-content;
        box-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .bot-bubble-container { display: flex; align-items: flex-start; margin: 5px 0; }
    .bot-avatar { font-size: 24px; margin-right: 8px; }
    .bot-bubble {
        background-color: #ffffff; color: black; padding: 10px 15px;
        border-radius: 15px; border-top-left-radius: 0;
        max-width: 80%; box-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    
    /* 判明した手がかりエリア */
    .clue-box {
        background-color: rgba(255, 255, 255, 0.3);
        padding: 15px; border-radius: 10px; margin-top: 20px;
        color: white;
    }
    .clue-item {
        display: inline-block;
        background-color: #4CAF50; color: white;
        padding: 5px 10px; margin: 3px; border-radius: 15px;
        font-size: 14px; font-weight: bold;
    }

    /* 初級者モード (ドリル風) */
    .question-box {
        background-color: #ffffff; padding: 20px; border-radius: 15px;
        text-align: center; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .question-label { font-size: 16px; color: #555; margin-bottom: 10px; }
    .question-text {
        font-size: 32px; font-weight: bold; color: #333; line-height: 1.3;
    }
    .feedback-msg {
        font-size: 24px; font-weight: bold; text-align: center;
        margin-top: 10px; padding: 10px; border-radius: 5px;
    }
    .feedback-good { color: #2e7d32; background-color: #e8f5e9; }
    .feedback-retry { color: #d32f2f; background-color: #ffebee; }
    .feedback-next { color: #1976d2; background-color: #e3f2fd; }

    [data-testid="stForm"] {
        background-color: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 10px;
    }
    
    /* Menuボタン */
    button[data-testid="stSidebarCollapsedControl"] {
        width: auto !important; height: auto !important; padding: 8px 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.8) !important; border-radius: 8px !important;
        background-color: rgba(255, 255, 255, 0.2) !important; color: white !important;
    }
    button[data-testid="stSidebarCollapsedControl"]::after {
        content: "Menu" !important; font-weight: bold !important; font-size: 16px !important;
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
        except json.JSONDecodeError as e:
            # ★ここでエラー内容を画面に出す！
            st.error(f"⚠️ {filename} の中身が壊れています！\n場所: {e}")
            return None
        except Exception as e:
            st.error(f"⚠️ {filename} を読み込めませんでした: {e}")
            return None
    else:
        st.error(f"⚠️ {filename} が見つかりません。")
        return None

def normalize_text(text):
    if not text: return ""
    text = re.sub(r'[.?,]+', ' ', text)
    return " ".join(text.split()).lower()

data = load_json(JSON_FILE)
template = load_json(TEMPLATE_FILE)
training_data = load_json(TRAINING_FILE)

if not data or not template or not training_data:
    st.error("エラー: 必要なJSONファイル(microwave, template, training)が不足しています。")
    st.stop()


# ==========================================
# 3. セッションステート初期化
# ==========================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [] 
if "found_clues" not in st.session_state:
    st.session_state.found_clues = [] # ★判明した手がかりリスト

# 初級用
if "training_cat_index" not in st.session_state:
    st.session_state.training_cat_index = 0
if "mistake_count" not in st.session_state:
    st.session_state.mistake_count = 0
if "last_feedback" not in st.session_state:
    st.session_state.last_feedback = ""
if "completed_phrases" not in st.session_state:
    st.session_state.completed_phrases = set()
if "current_category" not in st.session_state:
    st.session_state.current_category = training_data[0]["category"] if training_data else ""

# ==========================================
# 4. サイドバー (モード切替)
# ==========================================
with st.sidebar:
    st.title("Settings")
    mode = st.radio("Mode Select:", ["🔰 初級者 (Training)", "🔥 上級者 (Advanced)"])
    
    st.markdown("---")
    if st.button("Reset All"):
        st.session_state.chat_history = []
        st.session_state.found_clues = []
        st.session_state.completed_phrases = set()
        st.session_state.training_cat_index = 0
        st.session_state.mistake_count = 0
        st.session_state.last_feedback = ""
        st.rerun()

st.title("🔒 連想 Gamers Training App")

# パスワード認証
SECRET_PASSWORD_VAL = st.secrets.get("SECRET_PASSWORD", "2025") if os.environ.get("STREAMLIT_ENV") == "CLOUD" else "2025"
password = st.text_input("Password", type="password")
if password != SECRET_PASSWORD_VAL:
    st.stop()

# ==========================================
# 5. メイン画面 (モード分岐)
# ==========================================

# ---------------------------------------------------------
# 【A】初級者モード (変更なし・ドリル形式)
# ---------------------------------------------------------
if mode == "🔰 初級者 (Training)":
    
    categories = sorted(list(set(item["category"] for item in training_data)))
    if st.session_state.current_category not in categories:
         st.session_state.current_category = categories[0]
    selected_cat = st.selectbox("カテゴリー選択", categories, index=categories.index(st.session_state.current_category))

    if selected_cat != st.session_state.current_category:
        st.session_state.current_category = selected_cat
        st.session_state.training_cat_index = 0
        st.session_state.mistake_count = 0
        st.session_state.last_feedback = ""
        st.rerun()

    current_tasks = [t for t in training_data if t["category"] == selected_cat]
    
    if st.session_state.training_cat_index < len(current_tasks):
        target_task = current_tasks[st.session_state.training_cat_index]
        q_text = target_task["question"]
        
        st.markdown(f"""
        <div class="question-box">
            <div class="question-label">Q: Read this aloud!</div>
            <div class="question-text">{q_text}</div>
        </div>
        """, unsafe_allow_html=True)
        
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
        st.markdown("""<div class="question-box"><div class="question-text">🎉 Category Complete! 🎉</div></div>""", unsafe_allow_html=True)
        target_task = None
        if st.button("Retry this Category"):
            for t in current_tasks:
                kw = t.get("keyword")
                if kw in st.session_state.completed_phrases:
                    st.session_state.completed_phrases.remove(kw)
            st.session_state.training_cat_index = 0
            st.session_state.mistake_count = 0
            st.session_state.last_feedback = ""
            st.rerun()

    if target_task:
        with st.form(key='training_form', clear_on_submit=True):
            user_input = st.text_input("Voice/Text: 入力する", placeholder="上の英文を読んでください")
            submit_button = st.form_submit_button(label='送信する')

        if submit_button and user_input:
            clean_input = normalize_text(user_input)
            t_kw = target_task.get("keyword", "")
            t_q = target_task.get("question", "")
            if t_kw in clean_input or normalize_text(t_q) in clean_input:
                st.session_state.last_feedback = "Good!"
                st.session_state.completed_phrases.add(t_kw)
                st.session_state.training_cat_index += 1
                st.session_state.mistake_count = 0
            else:
                st.session_state.mistake_count += 1
                count = st.session_state.mistake_count
                if count == 1: st.session_state.last_feedback = "Retry"
                elif count == 2: st.session_state.last_feedback = "Almost"
                elif count >= 3:
                    st.session_state.last_feedback = "Skip"
                    st.session_state.training_cat_index += 1
                    st.session_state.mistake_count = 0
            st.rerun()

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
# 【B】上級者モード (シンプルUI + 脳みそ直結)
# ---------------------------------------------------------
else:
    st.header("🔥 実戦形式 (No Hint Mode)")
    st.caption("ヒントはありません。自分の言葉で質問して、正解を見つけよう！")
    
    # 1. チャット履歴
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

    # 2. 入力フォーム (シンプル)
    with st.form(key='gamer_form', clear_on_submit=True):
        user_input = st.text_input("Your Question:", placeholder="Ex: Is it bigger than your hand?")
        submit_button = st.form_submit_button(label='Send')

    # 3. 判定ロジック (★ここが重要: PC版と同じ判定方式)
    if submit_button and user_input:
        clean_input = normalize_text(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # 脳みそ(data["rules"])を直接検索
        found_key = None
        
        # 全カテゴリの全ルールを走査
        for category, rules in data["rules"].items():
            for keyword, answer_key in rules.items():
                # キーワードが入力文に含まれているか？
                if keyword in clean_input:
                    found_key = keyword
                    
                    # 回答を取得
                    raw_answer = data["response_map"].get(answer_key, answer_key)
                    if isinstance(raw_answer, list): # リストの場合はとりあえず最初の1つ
                        raw_answer = raw_answer[0]
                    
                    raw_answer = raw_answer.replace(".wav", "").upper()
                    
                    # 日本語表示用マップ
                    display_map = {
                        "YES": "Yes! (イエス)", 
                        "NO": "No. (ノー)", 
                        "PARTIAL_YES": "Partial Yes (部分的にイエス)",
                        "CORRECT": "Correct!! (正解！)", 
                        "USUALLY_YES": "Usually Yes (たいていそう)",
                        "DEPENS": "It depends (場合による)", 
                        "SOME_PEOPLE_USE": "Some people use it (使う人もいる)",
                        "SOME_ARE_YES": "Some are Yes (一部はイエス)", 
                        "CLOSE": "Close! (惜しい！)"
                    }
                    display_answer = display_map.get(raw_answer, raw_answer)
                    
                    # ポジティブな回答なら色を変える＆手がかりリストに追加
                    is_positive = any(k in raw_answer for k in ["YES", "CORRECT", "PARTIAL", "USUALLY", "SOME"])
                    status = "success" if is_positive else "error"
                    
                    # 結果をチャットに追加
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": f"{display_answer}", 
                        "status": status
                    })
                    
                    # ★正解に近い情報なら「手がかりリスト」に追加
                    if is_positive and found_key not in st.session_state.found_clues:
                        st.session_state.found_clues.append(found_key)
                        
                    break # 最初に見つけたキーワードで判定終了
            if found_key:
                break
        
        if not found_key:
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": "🤔 Sorry, I don't understand.", 
                "status": "warning"
            })
        
        st.rerun()

    # 4. 判明した手がかりリスト (画面下)
    if st.session_state.found_clues:
        st.markdown('<div class="clue-box">📝 <b>Found Clues (判明した手がかり):</b><br>', unsafe_allow_html=True)
        clue_html = ""
        for clue in st.session_state.found_clues:
            clue_html += f'<span class="clue-item">{clue}</span>'
        st.markdown(clue_html + '</div>', unsafe_allow_html=True)