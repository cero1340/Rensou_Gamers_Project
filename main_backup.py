import json
import os
import time
import keyboard  # キーボード操作用 (pip install keyboard が必要)

# ==========================================
# 1. 設定エリア
# ==========================================

# JSONファイル名（実際のファイル名に合わせてください）
JSON_FILE_NAME = "microwave_data.json"

# フォルダの場所
BASE_DIR = r"D:\Rensou_Gamers_Project"

# ファイル名設定
INPUT_TEXT_FILE = "current_question.txt"  # 読み込む質問ファイル
OUTPUT_PATH_FILE = "next_wav_path.txt"    # OBSに渡すWAVパスファイル
THINKING_FILE = "thinking_state.txt"      # 考え中表示の制御ファイル
AUDIO_DIR_NAME = "audio"                  # 音声ファイル置き場
DEFAULT_WAV = "again.wav"                 # キーワードヒットなしの場合の音声

# 一時停止キーの設定（F9キー）
PAUSE_HOTKEY = "f9"

# ==========================================
# 2. 機能（関数）の定義
# ==========================================

# 一時停止フラグ
is_paused = False

def toggle_pause(e):
    """キーが押されたら一時停止/再開を切り替える"""
    global is_paused
    is_paused = not is_paused
    if is_paused:
        print(f"\n[一時停止] システムを待機状態にしました。（解除は {PAUSE_HOTKEY} キー）")
    else:
        print(f"\n[再開] 監視を再開します。")

def load_rules():
    """JSONファイルを読み込む"""
    try:
        with open(os.path.join(BASE_DIR, JSON_FILE_NAME), 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"エラー: JSONファイルが読み込めません: {e}")
        return None

def find_response(text, data):
    """質問テキストからキーワードを探してWAVファイル名を返す"""
    text = text.lower()
    rules = []
    
    # ルールをリスト化して整理
    for cat, items in data.get("rules", {}).items():
        for k, v in items.items():
            rules.append((k.lower(), v))
    
    # 長いキーワードから先にチェックするように並べ替え
    rules.sort(key=lambda x: len(x[0]), reverse=True)
    
    # キーワードマッチング
    for k, v in rules:
        if k in text:
            print(f"★ヒット!: '{k}' -> 回答キー: {v}")
            return data.get("response_map", {}).get(v)
            
    print("キーワードが見つかりませんでした。")
    return DEFAULT_WAV

def write_file(filename, content):
    """ファイルに書き込む"""
    try:
        path = os.path.join(BASE_DIR, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"書き込みエラー: {e}")

# ==========================================
# 3. メイン処理
# ==========================================

def main():
    print("==========================================")
    print("   AI回答システム (OBS連携版) 起動")
    print(f"   ★ {PAUSE_HOTKEY} キーで一時停止/再開")
    print("==========================================")
    
    # キー監視を開始
    keyboard.on_press_key(PAUSE_HOTKEY, toggle_pause)

    # ルール読み込み
    data = load_rules()
    if not data:
        print("終了します。")
        return

    input_path = os.path.join(BASE_DIR, INPUT_TEXT_FILE)
    last_time = 0
    audio_dir = os.path.join(BASE_DIR, AUDIO_DIR_NAME)

    # 起動時の初期化（ファイルをリセット）
    write_file(OUTPUT_PATH_FILE, "")
    write_file(THINKING_FILE, "0")

    # 初回起動時に既存ファイルのタイムスタンプを取得して、古い質問への反応を防ぐ
    if os.path.exists(input_path):
        last_time = os.path.getmtime(input_path)

    try:
        while True:
            time.sleep(0.5) # CPU負荷軽減

            if not os.path.exists(input_path):
                continue
            
            # ファイルの更新日時をチェック
            mtime = os.path.getmtime(input_path)

            # ファイルが更新されていたら...
            if mtime > last_time:
                # まず「更新された」という事実だけを記録（これで再開時の暴発を防ぐ）
                last_time = mtime 

                # ★ここで一時停止チェック
                if is_paused:
                    print("（一時停止中のため、質問を無視しました）")
                    continue # ここで処理を中断して次のループへ

                # --- ここから先は「再開中」のみ実行される ---
                
                # 書き込み完了待ち
                time.sleep(0.1)
                
                # 1. 質問テキスト読み込み
                try:
                    with open(input_path, 'r', encoding='utf-8') as f:
                        text = f.read().strip()
                except:
                    continue

                if not text: continue
                print(f"\n質問を受信: {text}")

                # 2. 「考え中」表示ON
                write_file(THINKING_FILE, "1")
                print("演出: 考え中...")

                # 3. 演出用ウェイト (1.5秒)
                time.sleep(1.5)

                # 4. 回答の決定と送信
                wav = find_response(text, data)
                if wav:
                    full_path = os.path.normpath(os.path.join(audio_dir, wav))
                    write_file(OUTPUT_PATH_FILE, full_path)
                    print(f"OBSへ送信: {wav}")

                # 5. 「考え中」表示OFF
                write_file(THINKING_FILE, "0")

                # 6. 連続再生対応のためのリセット処理
                time.sleep(1.0)
                write_file(OUTPUT_PATH_FILE, "") 
                print("--- 待機状態へ ---")

    except KeyboardInterrupt:
        print("\nシステムを終了します。")

if __name__ == "__main__":
    main()