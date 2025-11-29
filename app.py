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

# フォント設定 (既存)
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
    """JSONファイルを読み込む関数"""
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            # st.errorは画面遷移ロジック外で使う
            print(f"Error loading {filename}: {e}")
            return None
    return None

# ページを 'game' 状態に切り替える関数
def switch_to_game():
    """ホーム画面からゲーム画面へ状態を切り替えるコールバック関数"""
    st.session_state.page = 'game'

# ==========================================
# 3. 初期化 & データ読み込み & 認証
# ==========================================

# ページの切り替え状態を管理する（初期値は 'home'）
if 'page' not in st.session_state:
    st.session_state.page = 'home'

st.title("🔒 連想 Gamers Training App")

# 環境変数がない場合のデフォルト値を使用
if os.environ.get("STREAMLIT_ENV") == "CLOUD":
    SECRET_PASSWORD_VAL = st.secrets.get("SECRET_PASSWORD", "2025")
else:
    SECRET_PASSWORD_VAL = "2025"

# パスワード認証 (既存)
password = st.text_input("Password", type="password")
if password != SECRET_PASSWORD_VAL:
    st.stop()
    
# 認証成功後のデータ読み込み
data = load_json(JSON_FILE)
template = load_json(TEMPLATE_FILE)

if not data or not template:
    st.error("データファイルが見つかりません。")
    st.stop()

# セッションステート初期化 (既存)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [] 

# ==========================================
# 4. 画面遷移ロジックの実行
# ==========================================

if st.session_state.page == 'home':
    # ----------------------------------------
    # 【ホーム画面】: 使い方ガイドとゲーム開始ボタンのみ表示
    # ----------------------------------------
    st.header("トレーニングを開始します")
    
    # ★ 使い方ガイド (既存のコード) ★
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
    
    # ゲーム開始ボタン
    st.button("🚀 ゲーム開始", on_click=switch_to_game, type="primary")

elif st.session_state.page == 'game':
    # ----------------------------------------
    # 【チャットゲーム画面】: チャットUIとして機能
    # ----------------------------------------
    st.header("💬 チャットゲーム開始！")
    
    # ==========================================
    # 4. チャット履歴の表示 (画面上部)
    # ==========================================
    # LINE風の見た目を維持するため、st.success/errorの代わりに絵文字とmarkdownを使用
    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            with st.chat_message("user", avatar="😊"):
                st.write(chat["content"])
        elif chat["role"] == "assistant":
            with st.chat_message("assistant", avatar="🤖"):
                content = chat["content"]
                status = chat.get("status")
                
                # ステータスに応じて絵文字と色で強調
                if status == "success":
                    # Yes/Correct の場合 (緑色🟢)
                    st.markdown(f"🟢 {content}")
                elif status == "error":
                    # No の場合 (赤色🔴)
                    st.markdown(f"🔴 {content}")
                else:
                    # Warning/その他 の場合 (黄色🟡)
                    st.markdown(f"🟡 {content}")

    st.divider()

    # ==========================================
    # 5. 入力エリア (画面下部) - 既存のロジックを維持
    # ==========================================

    # --- カテゴリ選択 ---
    step_list = list(template.keys())
    current_step_label = st.selectbox("カテゴリー選択", step_list)

    step_data = template[current_step_label]
    question_prefix = step_data["question"]
    options_dict = step_data["options"]

    # Q: ... の表示
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
        # AIの思考中をシミュレート
        with st.spinner("AIが考え中..."):
            time.sleep(1.5) 
            
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
                    # .wavを除去し、すべて大文字に変換
                    display_answer = data["response_map"].get(answer_key, answer_key).replace(".wav", "").upper()
                    # YES/CORRECT が含まれていれば success (緑色)
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
            
            # 画面を更新
            st.rerun()