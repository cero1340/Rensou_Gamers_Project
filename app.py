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
# ★ LINE風デザインCSSの適用（入力欄固定版） ★
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Yuji+Syuku&display=swap');
    
    /* 全体のフォント設定 */
    html, body, [class*="css"] {
        font-family: 'Helvetica Neue', 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', Arial, sans-serif;
    }
    h1 { font-family: 'Yuji Syuku', serif !important; font-weight: 400; }

    /* LINE風 背景色 (ブルーグレー) */
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

    /* Expanderの背景を白くして読みやすく */
    .streamlit-expanderContent {
        background-color: white;
        border-radius: 0 0 10px 10px;
        padding: 10px;
    }
    .streamlit-expanderHeader {
        background-color: white;
        border-radius: 10px 10px 0 0;
    }

    /* ▼▼▼ 追加：入力フォームを画面下に固定する設定 ▼▼▼ */
    
    /* フォーム自体を画面最下部に固定 */
    [data-testid="stForm"] {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #f0f2f6; /* 背景色をつけてチャットと区別 */
        padding: 15px 20px;
        z-index: 9999; /* 最前面に表示 */
        border-top: 2px solid #ddd;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
    }
    
    /* フォームの中身のレイアウト調整 */
    [data-testid="stForm"] > div {
        max-width: 800px; /* PCで見やすく幅制限 */
        margin: 0 auto;
    }

    /* チャットエリアの下部に余白を作り、フォームで隠れないようにする */
    .main .block-container {
        padding-bottom: 400px !important;
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
    """ホーム画面からゲーム画面へ状態を切り替えるコールバック関数"""
    st.session_state.page = 'game'

# ==========================================
# 3. 初期化 & データ読み込み & 認証
# ==========================================

if 'page' not in st.session_state:
    st.session_state.page = 'home'

# サイドバーに設定とタイトルを表示
with st.sidebar:
    st.title("連想 Training 🎮")
    st.markdown("---")

if os.environ.get("STREAMLIT_ENV") == "CLOUD":
    SECRET_PASSWORD_VAL = st.secrets.get("SECRET_PASSWORD", "2025")
else:
    SECRET_PASSWORD_VAL = "2025"

# パスワード認証 (サイドバーではなくメイン画面で最初だけ行う)
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Login")
    password = st.text_input("Password", type="password")
    if password == SECRET_PASSWORD_VAL:
        st.session_state.authenticated = True
        st.rerun()
    else:
        if password:
            st.error("Incorrect password")
        st.stop()

# データの読み込み
data = load_json(JSON_FILE)
template = load_json(TEMPLATE_FILE)

if not data or not template:
    st.error("データファイルが見つかりません。")
    st.stop()

# チャット履歴の初期化
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [] 

# ==========================================
# 4. 画面遷移ロジックの実行
# ==========================================

if st.session_state.page == 'home':
    # ----------------------------------------
    # 【ホーム画面】
    # ----------------------------------------
    st.header("トレーニングを開始します")
    
    with st.expander("📖 遊び方 / How to Play (クリックで開く)", expanded=True):
        st.markdown("""
        **このアプリは、AI相手に英語で質問をして「正解のアイテム」を当てるゲームです。**
        
        1. **カテゴリを選ぶ**
            - 左のサイドバーから「場所」や「素材」などを選びます。
            - ゲーム画面の下に質問のヒントが表示されます。
            
        2. **質問を入力する (2つの方法)**
            - 🎤 **A. 自分で聞く :** - マイク入力などで、自分で英文を作って質問してみましょう。
            - 📝 **B. リストから選ぶ :** - リストからキーワードを選んで質問できます。
            
            【注意点】必ず「英語キーボード」にして下さい。

        3. **送信 (Submit)**
            - **Yes** なら緑色🟢、**No** なら赤色🔴 で履歴に残ります。
        """)

    st.markdown("---")
    st.button("🚀 ゲーム開始", on_click=switch_to_game, type="primary")

elif st.session_state.page == 'game':
    # ----------------------------------------
    # 【チャットゲーム画面】
    # ----------------------------------------
    st.header("💬 チャットゲーム開始！")
    
    # --- カテゴリ選択 (サイドバーに移動) ---
    with st.sidebar:
        st.header("⚙️ 設定 / Settings")
        step_list = list(template.keys())
        current_step_label = st.selectbox("カテゴリー選択", step_list)
        
        st.markdown("---")
        st.markdown("**Hints:**")
        # サイドバーにもヒントを出しておく
        step_data = template[current_step_label]
        question_prefix = step_data["question"]
        options_dict = step_data["options"]
        st.info(f"Q: {question_prefix} ... ?")

    # ==========================================
    # 4. チャット履歴の表示
    # ==========================================
    # チャット履歴を表示するコンテナ
    chat_container = st.container()
    with chat_container:
        for chat in st.session_state.chat_history:
            if chat["role"] == "user":
                # ユーザーの発言 (右側・緑)
                st.markdown(f"""
                <div class="user-bubble">
                    {chat["content"]}
                </div>
                """, unsafe_allow_html=True)
                
            elif chat["role"] == "assistant":
                # AIの発言 (左側・白)
                content = chat["content"]
                status = chat.get("status")
                
                # アイコンと色
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
    # 5. 入力エリア (画面下に固定)
    # ==========================================

    # --- 入力フォーム ---
    # CSSで [data-testid="stForm"] をbottom:0に固定しています
    with st.form(key='game_form', clear_on_submit=True):
        
        # ヒントをフォーム内にも表示（入力時に見えるように）
        st.markdown(f"**Hint:** `{question_prefix} ... ?`")

        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 1. 自分で入力
            user_input = st.text_input(
                "Voice/Text Input",
                placeholder=f"Ex: {question_prefix} house?",
                label_visibility="collapsed" # ラベルを隠してスッキリさせる
            )

        with col2:
            # 2. リストから選ぶ
            option_labels = ["(List)"] + list(options_dict.keys())
            selected_option_label = st.selectbox("Select", option_labels, label_visibility="collapsed")
        
        # 送信ボタン
        submit_button = st.form_submit_button(label='送信 / Submit', type="primary")

    # ==========================================
    # 6. 判定ロジック
    # ==========================================
    if submit_button:
        with st.spinner("AI thinking..."):
            time.sleep(1.0) 
            
            search_keyword = None
            display_question = ""

            # A. 自分で入力した場合
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
                
            # B. リストから選んだ場合
            elif selected_option_label != "(List)":
                val_obj = options_dict[selected_option_label]
                search_keyword = val_obj["keyword"]
                display_question = f"{question_prefix} {selected_option_label}?"

            # --- 判定処理 ---
            if search_keyword:
                st.session_state.chat_history.append({
                    "role": "user", "content": display_question
                })

                all_rules = {}
                for cat in data["rules"].values():
                    all_rules.update(cat)
                
                if search_keyword in all_rules:
                    answer_key = all_rules[search_keyword]
                    raw_answer = data["response_map"].get(answer_key, answer_key).replace(".wav", "").upper()
                    
                    # 日本語変換マップ
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
                    
                    # 修正: <b>タグで太字表示
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