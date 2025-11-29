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
# ★ LINE風デザインCSSの適用 ★
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

    /* 入力フォーム周りの背景を少し見やすく */
    [data-testid="stForm"] {
        background-color: rgba(255, 255, 255, 0.9);
        padding: 20px;
        border-radius: 10px;
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

    /* スクロールコンテナの背景調整 */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
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

st.title("🔒 連想 Gamers Training App")

if os.environ.get("STREAMLIT_ENV") == "CLOUD":
    SECRET_PASSWORD_VAL = st.secrets.get("SECRET_PASSWORD", "2025")
else:
    SECRET_PASSWORD_VAL = "2025"

# パスワード認証
password = st.text_input("Password", type="password")
if password != SECRET_PASSWORD_VAL:
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
            - 上のメニューから「場所」や「素材」などを選びます。
            - すると `Q: ...` の横に、質問の定型文（ヒント）が表示されます。
            
        2. **質問を入力する (2つの方法)**
            - 🎤 **A. 自分で聞く :** - マイク入力などで、自分で英文を作って質問してみましょう。
            - 例: `Is it made of metal?`
            - 📝 **B. リストから選ぶ :** - 思いつかない時は、リストからキーワードを選んで質問できます。
            
            【注意点】必ず「英語キーボード」にして下さい。

        3. **送信 (Submit)**
            - ボタンを押すとAIが答えます。
            - **Yes** なら緑色🟢、**No** なら赤色🔴 で履歴に残ります。
            
        ---
        🗣️ **Point:** 声に出して質問する練習をしていけば、必ず「連想型スピーキング」が身に付きます！まずは「初級編」から初めて、慣れてきたら「上級編」にチャレンジして下さい！
        """)

    st.markdown("---")
    st.button("🚀 ゲーム開始", on_click=switch_to_game, type="primary")

elif st.session_state.page == 'game':
    # ----------------------------------------
    # 【チャットゲーム画面】
    # ----------------------------------------
    st.header("💬 チャットゲーム開始！")
    
    # ==========================================
    # 4. チャット履歴の表示 (スクロール固定枠を使用)
    # ==========================================
    # ★重要変更★ height=500の枠を作り、その中だけで会話をスクロールさせる
    with st.container(height=500):
        for chat in st.session_state.chat_history:
            if chat["role"] == "user":
                # ユーザーの発言 (右側・緑)
                st.markdown(f"""
                <div class="user-bubble">
                    {chat["content"]}
                </div>
                """, unsafe_allow_html=True)
                
            elif chat["role"] == "assistant":
                # AIの発言 (左側・白・アイコン付き)
                content = chat["content"]
                status = chat.get("status")
                
                # ステータスに応じた装飾テキストの作成
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

    # st.divider() # 枠の中に区切り線は不要なので削除

    # ==========================================
    # 5. 入力エリア (枠の下に固定される)
    # ==========================================

    # --- カテゴリ選択 ---
    step_list = list(template.keys())
    current_step_label = st.selectbox("カテゴリー選択", step_list)

    step_data = template[current_step_label]
    question_prefix = step_data["question"]
    options_dict = step_data["options"]

    st.markdown(f"### Q: {question_prefix} ... ?")

    # --- 入力フォーム ---
    with st.form(key='game_form', clear_on_submit=True):
        
        # 1. 自分で入力
        user_input = st.text_input(
            "Voice/Text: 入力する",
            placeholder=f"Ex: {question_prefix} house?"
        )

        # 2. リストから選ぶ (Hint List)
        option_labels = ["(Select from list)"] + list(options_dict.keys())
        selected_option_label = st.selectbox("Hint List: 選択する", option_labels)
        
        # 送信ボタン
        submit_button = st.form_submit_button(label='送信する')

    # ==========================================
    # 6. 判定ロジック
    # ==========================================
    if submit_button:
        with st.spinner("AIが考え中..."):
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
            elif selected_option_label != "(Select from list)":
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
                    # ファイル名(.wav)を除去してキーを取得
                    raw_answer = data["response_map"].get(answer_key, answer_key).replace(".wav", "").upper()
                    
                    # ★ 表示用の日本語変換マップ ★
                    display_map = {
                        "YES": "イエス！",
                        "NO": "ノー！",
                        "PARTIAL_YES": "部分的にはイエス！",
                        "CORRECT": "正解！",
                        "USUALLY_YES": "通常はイエスかな！",
                        "DEPENS": "状況によるよ！",
                        "SOME_PEOPLE_USE": "使う人もいるよ！"
                    }
                    
                    # マップにあれば日本語に、なければそのまま表示
                    display_answer = display_map.get(raw_answer, raw_answer)
                    
                    # 緑色にする条件: YES, CORRECT, PARTIAL_YES, USUALLY_YES
                    is_positive = any(k in raw_answer for k in ["YES", "CORRECT", "PARTIAL"])
                    status = "success" if is_positive else "error"
                    
                    # ★太字修正済み (<b>タグ) ★
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