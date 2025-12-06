import json
import os
import time
import re

# === 設定エリア ===
JSON_FILE_NAME = "microwave_data.json"
BASE_DIR = r"D:\Rensou_Gamers_Project"

INPUT_TEXT_FILE = "current_question.txt"
OUTPUT_PATH_FILE = "next_wav_path.txt"
THINKING_FILE = "thinking_state.txt"
VIDEO_TRIGGER_FILE = "video_trigger.txt" # ★追加: 動画再生用のトリガーファイル
AUDIO_DIR_NAME = "audio"
DEFAULT_WAV = "none.wav"

# ファイル書き込み関数
def write_file(filename, content):
    """指定されたファイルに内容を書き込む"""
    try:
        path = os.path.join(BASE_DIR, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"書き込みエラー: {e}")

# JSON読み込み関数
def load_rules():
    """JSONファイルからルールデータを読み込む"""
    try:
        json_path = os.path.join(BASE_DIR, JSON_FILE_NAME)
        print(f"JSON読み込み中: {json_path}")
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"★JSON読み込み失敗: {e}")
        return None

# 回答検索関数
def find_response(text, data):
    """質問テキストとJSONルールを照合し、回答WAVファイル名を決定する"""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text) 
    text = re.sub(r'\s+', ' ', text).strip()
    
    rules = []
    
    for cat, items in data.get("rules", {}).items():
        for k, v in items.items():
            if cat == "category_answer":
                rules.append((k.lower(), v, 'EXACT'))
            else:
                rules.append((k.lower(), v, cat))
    
    rules.sort(key=lambda x: len(x[0]), reverse=True)
    
    for k, v, cat in rules:
        if cat == 'EXACT':
            if k == text:
                print(f"ヒットしました: [完全一致] '{k}' -> Key: '{v}'")
                pass
            else:
                continue
        elif k in text:
            print(f"ヒットしました: [部分一致:{cat}] '{k}' -> Key: '{v}'")
            pass
        else:
            continue
            
        wav_file = data.get("response_map", {}).get(v)
        
        if wav_file:
            return wav_file
        
        if v.endswith(".wav"):
            return v
        
        print(f"★警告: Key '{v}' に対応するWAVファイルが response_map にありません。")
        return DEFAULT_WAV
            
    print("ヒットするキーワードがありませんでした。")
    return DEFAULT_WAV

def main():
    print("=== AI回答システム Ver 1.4 (動画連携対応) ===")
    print("初期化中...")

    # ルール読み込み
    data = load_rules()
    if not data:
        print("プログラムを終了します。JSONファイルを確認してください。")
        time.sleep(10)
        return

    input_path = os.path.join(BASE_DIR, INPUT_TEXT_FILE)
    audio_dir = os.path.join(BASE_DIR, AUDIO_DIR_NAME)
    
    # 初期化：各種ファイルをリセット
    write_file(OUTPUT_PATH_FILE, "")
    write_file(THINKING_FILE, "0")
    write_file(VIDEO_TRIGGER_FILE, "0") # ★追加: 動画トリガーを初期化
    
    last_time = 0.0
    if os.path.exists(input_path):
        last_time = os.path.getmtime(input_path)

    print("準備完了。OBSのF9ホットキーを押して、ゲームを開始してください。")

    try:
        while True:
            time.sleep(0.1)

            if not os.path.exists(input_path):
                continue

            try:
                mtime = os.path.getmtime(input_path)
            except:
                continue

            if mtime > last_time:
                last_time = mtime
                time.sleep(0.1) 
                
                try:
                    with open(input_path, 'r', encoding='utf-8') as f:
                        text = f.read().strip()
                except:
                    continue

                if not text: continue
                
                print(f"\n[質問検知] {text}")

                # 1. OBSに「考え中」を表示させる
                write_file(THINKING_FILE, "1")
                
                time.sleep(1.5)

                # 2. 回答を決める
                wav = find_response(text, data)
                
                if wav:
                    full_path = os.path.normpath(os.path.join(audio_dir, wav))
                    print(f"[回答指示] {wav}")
                    
                    # ★追加: もし正解(correct.wav)なら、動画再生フラグを立てる
                    # (JSONの設定に合わせてwavファイル名で判定)
                    if wav == "correct.wav":
                        print("★正解を検知！動画再生指示を送ります。")
                        write_file(VIDEO_TRIGGER_FILE, "1")
                    
                    # 3. OBSにWAVパスを渡す
                    write_file(OUTPUT_PATH_FILE, full_path)
                
                # 4. OBSの「考え中」を消す
                write_file(THINKING_FILE, "0")

                time.sleep(1.0)
                write_file(OUTPUT_PATH_FILE, "")
                write_file(VIDEO_TRIGGER_FILE, "0") # ★追加: 動画トリガーを戻す

    except KeyboardInterrupt:
        print("\nシステムを終了します。")
        write_file(THINKING_FILE, "0")
        write_file(VIDEO_TRIGGER_FILE, "0")

if __name__ == "__main__":
    main()