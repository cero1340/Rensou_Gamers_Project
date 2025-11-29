import streamlit as st
import json
import os
import time

# ==========================================
# 1. 設定エリア
# ==========================================
JSON_FILE = "microwave_data.json"
TEMPLATE_FILE = "Questions_template.json" 

st.set_page_config(page_title="連想 Training", page_icon="🎮")

# ==========================================
# ★ LINE風デザインCSS ＋ 下詰め強制レイアウト ★
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Yuji+Syuku&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Helvetica Neue', 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', Arial, sans-serif;
    }
    h1 { font-family: 'Yuji Syuku', serif !important; font-weight: 400; }
    
    /* LINE風 背景色 */
    .stApp {
        background-color: #7494c0;
    }

    /* ★チャット全体を包む箱（スクロールエリア）★ */
    .chat-scroll-area {
        height: 500px;            /* 高さ固定 */
        overflow-y: auto;         /* スクロール可能に */
        display: flex;            /* フレックスボックス化 */
        flex-direction: column-reverse; /* 【重要】下から順に積み上げる設定 */
        padding: 20px;
        background-color: rgba(255, 255, 255, 0.1); 
        border-radius: 10px;
        margin-bottom: 20px;
    }

    /* ユーザーの吹き出し */
    .user-bubble {
        background-color: #98e165;
        color: black;
        padding: 10px 15px;
        border-radius: 15px;
        border-top-right-radius: 0;
        margin: 5px 0 5px auto; /* 右寄せ */
        max-width: 80%;
        width: fit-content;
        box-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        text-align: left;
        line-height: 1.5;
    }

    /* AIの吹き出し */
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

    /* フォーム周りの装飾 */
    [data-testid="stForm"] {
        background-color: rgba(255, 255, 255, 0.9);
        padding: 20px;
        border-radius: 10px;
    }
    
    .streamlit-expanderContent {
        background-color: white;
        border-radius: 0 0 10px 10px;
        padding: 10px;
    }
    .streamlit-expanderHeader {
        background-color: white;
        border-radius: 10px 10px 0 0;
    }

    /* ▼▼▼ フォント調整・レイアウト修正箇所 ▼▼▼ */
    .category-label {
        font-size: 14px;
        font-weight: bold;
        color: #333;
        margin-bottom: 10px;
    }
    
    .question-text {
        font-size: 35px;      /* ★修正: 28px -> 35px に大幅アップ */
        font-weight: bold;
        color: #FFFF00;       /* 鮮やかな黄色 */
        margin-top: 0px;
        margin-bottom: 15px;
        line-height: 1.2;     /* 行間を少し詰めてまとまりよく */
        text-shadow: 2px 2px 0px #333333; /* 黒い影で視認性確保 */
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
            print(f"Error loading {filename}: {e}")
            return None
    return None

def switch_to_game():
    st.session_state.page = 'game'

# ==========================================
# 3. 初期化 & データ読み込み
# ==========================================

if 'page' not in st.session_state:
    st.session_state.page = 'home'

st.title("🔒 連想 Gamers Training App")

if os.environ.get("STREAMLIT_ENV") == "CLOUD":
    SECRET_PASSWORD_VAL = st.secrets.get("SECRET_PASSWORD", "2025")
else:
    SECRET_PASSWORD_VAL = "2025"

password = st.text_input("Password", type="password")
if password != SECRET_PASSWORD_VAL:
    st.stop()
    
data = load_json(JSON_FILE)
template = load_json(TEMPLATE_FILE)

if not data or not template:
    st.error("データファイルが見つかりません。")
    st.stop()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [] 

# ==========================================
# 4. 画面遷移ロジック
# ==========================================

if st.session_state.page == 'home':
    st.header("トレーニングを開始します")
    with st.expander("📖 遊び方 / How to Play", expanded=True):
        st.markdown("""
        **最新のメッセージが常に一番下（青いライン）に表示されます！**
        
        1. **カテゴリを選ぶ**
        2. **質問を入力**
        3. **送信** → チャットの一番下に表示され、古いものは上に移動します。
        """)
    st.markdown("---")
    st.button("🚀 ゲーム開始", on_click=switch_to_game, type="primary")

elif st.session_state.page == 'game':
    st.header("💬 チャットゲーム開始！")
    
    # ==========================================
    # 4. チャット履歴の表示
    # ==========================================
    chat_html = '<div class="chat-scroll-area">'
    
    for chat in reversed(st.session_state.chat_history):
        if chat["role"] == "user":
            chat_html += f'<div class="user-bubble">{chat["content"]}</div>'
        elif chat["role"] == "assistant":
            content = chat["content"]
            status = chat.get("status")
            display_text = content
            if status == "success":
                display_text = f"🟢 {content}"
            elif status == "error":
                display_text = f"🔴 {content}"
            else:
                display_text = f"🟡 {content}"
            
            chat_html += f'''
            <div class="bot-bubble-container">
                <div class="bot-avatar">🤖</div>
                <div class="bot-bubble">{display_text}</div>
            </div>
            '''
    
    chat_html += '</div>'
    st.markdown(chat_html, unsafe_allow_html=True)

    # ==========================================
    # 5. 入力エリア (カテゴリ選択のレイアウト変更)
    # ==========================================
    
    step_list = list(template.keys())

    if "selected_category_key" not in st.session_state:
        st.session_state.selected_category_key = step_list[0]

    st.markdown('<p class="category-label">カテゴリー選択</p>', unsafe_allow_html=True)

    current_cat = st.session_state.selected_category_key
    step_data = template[current_cat]
    question_prefix = step_data["question"]
    options_dict = step_data["options"]

    # ★Q: ... をさらに大きく強調★
    st.markdown(f'<p class="question-text">Q: {question_prefix} ... ?</p>', unsafe_allow_html=True)

    # 選択ボックス (ラベルは隠す)
    st.selectbox(
        "hidden_label", 
        step_list, 
        key="selected_category_key", 
        label_visibility="collapsed"
    )

    # 入力フォーム
    with st.form(key='game_form', clear_on_submit=True):
        user_input = st.text_input("Voice/Text: 入力する", placeholder=f"Ex: {question_prefix} house?")
        option_labels = ["(Select from list)"] + list(options_dict.keys())
        selected_option_label = st.selectbox("Hint List: 選択する", option_labels)
        submit_button = st.form_submit_button(label='送信する')

    # ==========================================
    # 6. 判定ロジック
    # ==========================================
    if submit_button:
        with st.spinner("AIが考え中..."):
            time.sleep(0.5)
            
            search_keyword = None
            display_question = ""

            if user_input:
                input_text = user_input.lower()
                display_question = user_input
                found = False
                for s_content in template.values():
                    for label, val_obj in s_content["options"].items():
                        kw = val_obj["keyword"]
                        if kw in input_text or label.lower() in input_text:
                            search_keyword = kw
                            found = True
                            break
                    if found: break
                
                if not search_keyword:
                    st.session_state.chat_history.append({"role": "user", "content": user_input})
                    st.session_state.chat_history.append({"role": "assistant", "content": "🤔 Sorry, I didn't catch that.", "status": "warning"})
                
            elif selected_option_label != "(Select from list)":
                val_obj = options_dict[selected_option_label]
                search_keyword = val_obj["keyword"]
                display_question = f"{question_prefix} {selected_option_label}?"

            if search_keyword:
                st.session_state.chat_history.append({"role": "user", "content": display_question})

                all_rules = {}
                for cat in data["rules"].values():
                    all_rules.update(cat)
                
                if search_keyword in all_rules:
                    answer_key = all_rules[search_keyword]
                    raw_answer = data["response_map"].get(answer_key, answer_key).replace(".wav", "").upper()
                    
                    display_map = {
                        "YES": "イエス！",
                        "NO": "ノー！",
                        "PARTIAL_YES": "部分的にはイエス！",
                        "CORRECT": "正解！",
                        "USUALLY_YES": "通常はイエスかな！",
                        "DEPENS": "状況によるよ！",
                        "SOME_PEOPLE_USE": "使う人もいるよ！"
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
            
            st.rerun()