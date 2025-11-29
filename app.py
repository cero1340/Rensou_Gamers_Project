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
# ★ LINE風デザインCSS ＋ 下から積み上げ設定 ★
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Yuji+Syuku&display=swap');
    
    /* 全体のフォント設定 */
    html, body, [class*="css"] {
        font-family: 'Helvetica Neue', 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', Arial, sans-serif;
    }
    h1 { font-family: 'Yuji Syuku', serif !important; font-weight: 400; }

    /* LINE風 背景色 */
    .stApp {
        background-color: #7494c0;
    }

    /* ユーザーの吹き出し (右側・緑色) */
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
        display: block;
    }

    /* AIの吹き出し (左側・白色) */
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
    }

    /* 入力フォーム周りの装飾 */
    [data-testid="stForm"] {
        background-color: rgba(255, 255, 255, 0.9);
        padding: 20px;
        border-radius: 10px;
    }
    
    /* Expanderの装飾 */
    .streamlit-expanderContent {
        background-color: white;
        border-radius: 0 0 10px 10px;
        padding: 10px;
    }
    .streamlit-expanderHeader {
        background-color: white;
        border-radius: 10px 10px 0 0;
    }

    /* スクロール枠の背景 */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }

    /* ★★★ ここが魔法のコード：下から積み上げ式にする設定 ★★★ */
    /* 枠の中身の重力を「下」にするイメージ */
    [data-testid="stVerticalBlockBorderWrapper"] > div > [data-testid="stVerticalBlock"] {
        display: flex;
        flex-direction: column-reverse;
    }

</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 関数定義
# ==========================================
def load_json(filename):
    """JSONファイルを読み込む関数"""
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
# 3. 初期化 & データ読み込み & 認証
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
    # --- ホーム画面 ---
    st.header("トレーニングを開始します")
    
    with st.expander("📖 遊び方 / How to Play", expanded=True):
        st.markdown("""
        **このアプリは、AI相手に英語で質問をして「正解のアイテム」を当てるゲームです。**
        
        1. **カテゴリを選ぶ**
        2. **質問を入力する (声 or テキスト)**
        3. **AIが回答** (Yes/No)
        
        **Latest Message is Always at the Bottom!**
        新しいメッセージは常に一番下（入力欄のすぐ上）に表示され、古いものは上に押し上げられます。
        """)

    st.markdown("---")
    st.button("🚀 ゲーム開始", on_click=switch_to_game, type="primary")

elif st.session_state.page == 'game':
    # --- ゲーム画面 ---
    st.header("💬 チャットゲーム開始！")
    
    # ==========================================
    # 4. チャット履歴の表示 (ウィンドウ形式・下から積み上げ)
    # ==========================================
    # height=550の枠を作り、CSSで「下から積み上げ」を適用済み
    # 中身が少ないときは一番下(Line 1)に表示され、増えると上に伸びていきます
    with st.container(height=550):
        
        # CSSで順序を反転(column-reverse)させているため、
        # プログラム側では「新しい順」に描画すると、見た目上で
        # [一番下] = 最新
        # [その上] = 1つ前
        # となります。
        for chat in reversed(st.session_state.chat_history):
            if chat["role"] == "user":
                # ユーザー (右・緑)
                st.markdown(f"""
                <div class="user-bubble">
                    {chat["content"]}
                </div>
                """, unsafe_allow_html=True)
                
            elif chat["role"] == "assistant":
                # AI (左・白)
                content = chat["content"]
                status = chat.get("status")
                
                display_text = content
                if status == "success":
                    display_text = f"🟢 {content}"
                elif status == "error":
                    display_text = f"🔴 {content}"
                else:
                    display_text = f"🟡 {content}"

                st.markdown(f"""
                <div class="bot-bubble-container">
                    <div class="bot-avatar">🤖</div>
                    <div class="bot-bubble">
                        {display_text}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ==========================================
    # 5. 入力エリア (ウィンドウの下に配置・固定はしない)
    # ==========================================
    # 上のチャット枠の高さが固定なので、この入力欄の位置は動きません

    step_list = list(template.keys())
    current_step_label = st.selectbox("カテゴリー選択", step_list)
    step_data = template[current_step_label]
    question_prefix = step_data["question"]
    options_dict = step_data["options"]

    st.markdown(f"### Q: {question_prefix} ... ?")

    with st.form(key='game_form', clear_on_submit=True):
        
        user_input = st.text_input(
            "Voice/Text: 入力する",
            placeholder=f"Ex: {question_prefix} house?"
        )

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