import json
import os
import time
import re
import threading
import keyboard  # pip install keyboard が必要

# === 設定エリア ===
JSON_FILE_NAME = "microwave_data.json"
BASE_DIR = r"D:\Rensou_Gamers_Project"

INPUT_TEXT_FILE = "current_question.txt"
OUTPUT_PATH_FILE = "next_wav_path.txt"
THINKING_FILE = "thinking_state.txt"
VIDEO_TRIGGER_FILE = "video_trigger.txt"

# ★変更: 履歴ファイルを左右2つに分ける
HISTORY_FILE_LEFT = "yes_history_left.txt"   # 左列用
HISTORY_FILE_RIGHT = "yes_history_right.txt" # 右列用
MAX_HISTORY_LINES = 25 # ★変更: 25行たまったら右列に行く（合計50行対応）

AUDIO_DIR_NAME = "audio"
DEFAULT_WAV = "none.wav"

# ★履歴管理用のリスト（メモリ上で保持）
yes_history_list = []

# ★YesとみなすWAVファイルリスト
POSITIVE_WAVS = [
    "yes.wav",
    "strong_yes.wav",
    "amazing_question_yes.wav",
    "triple_yes.wav",
    "yes_ofcourse.wav",
    "si.wav",
    "usually_yes.wav",
    "some_are_yes.wav",
    "some_are_yes_1.wav",
    "some_are_yes_2.wav",
    "some_are_yes_3.wav",
    "some_people_use.wav",
    "some_people_can_find.wav",
    "big_partial_yes.wav",
    "partial_yes.wav",
    "correct.wav"
]

# ★マニュアル操作設定
# キー: (ログ用メモ, 再生するWAVファイル名)
KEY_MAPPINGS = {
    "num 1": ("そうだね！", "yes.wav"),
    "num 2": ("たしかに", "usually_yes.wav"),
    "num 3": ("なるほど！", "strong_yes.wav"),
    "num 4": ("うーん...", "depends.wav"),
    "num 5": ("ちがうよ", "no.wav"),
    "num 0": ("正解！！", "correct.wav")
}

IGNORE_TEXTS = ["考え中...", ""]
is_reacting = False

# ファイル書き込み関数
def write_file(filename, content):
    """指定されたファイルに内容を書き込む"""
    try:
        path = os.path.join(BASE_DIR, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"書き込みエラー: {e}")

# ★履歴更新関数（左右分割対応）
def update_history_files(new_text=None):
    """リストを更新し、左右のファイルに振り分けて保存する"""
    global yes_history_list
    
    # 新しいテキストがあればリストに追加
    if new_text:
        # 見やすいように中黒(・)をつける
        yes_history_list.append(f"・{new_text}")
        print(f"[履歴追加] {new_text}")

    # リストを分割 (MAX_HISTORY_LINES = 25 で分割)
    left_content_list = yes_history_list[:MAX_HISTORY_LINES]
    right_content_list = yes_history_list[MAX_HISTORY_LINES:]

    # 文字列に結合
    left_text = "\n".join(left_content_list)
    right_text = "\n".join(right_content_list)

    # 左右それぞれのファイルに書き込み
    write_file(HISTORY_FILE_LEFT, left_text)
    write_file(HISTORY_FILE_RIGHT, right_text)

# JSON読み込み関数
def load_rules():
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
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text) 
    text = re.sub(r'\s+', ' ', text).strip()
    
    rules = []
    for cat, items in data.get("rules", {}).items():
        for k, v in items.items():
            rules.append((k.lower(), v, cat))
    
    rules.sort(key=lambda x: len(x[0]), reverse=True)
    
    for k, v, cat in rules:
        if k in text:
            print(f"ヒットしました: [{cat}] '{k}' -> Key: '{v}'")
            wav_file = data.get("response_map", {}).get(v)
            if wav_file: return wav_file
            if v.endswith(".wav"): return v
            return DEFAULT_WAV
            
    print("ヒットするキーワードがありませんでした。")
    return DEFAULT_WAV

# マニュアル演出関数
def manual_reaction_trigger(log_text, wav_name):
    global is_reacting
    if is_reacting: return 

    is_reacting = True
    print(f"\n[マニュアル操作] キー検知: （{log_text}） -> {wav_name}")

    audio_dir = os.path.join(BASE_DIR, AUDIO_DIR_NAME)
    full_path = os.path.normpath(os.path.join(audio_dir, wav_name))

    try:
        write_file(INPUT_TEXT_FILE, "考え中...")
        write_file(THINKING_FILE, "1")
        time.sleep(1.0) 
        write_file(INPUT_TEXT_FILE, "") 
        
        if wav_name == "correct.wav":
             write_file(VIDEO_TRIGGER_FILE, "1")

        write_file(OUTPUT_PATH_FILE, full_path)
        time.sleep(0.2)
        write_file(THINKING_FILE, "0")
        time.sleep(1.0)
        write_file(OUTPUT_PATH_FILE, "")
        write_file(VIDEO_TRIGGER_FILE, "0")
        
    except Exception as e:
        print(f"マニュアル操作エラー: {e}")
    finally:
        is_reacting = False

def main():
    print("=== AI回答システム Ver 1.9 (履歴25行分割版) ===")
    print("初期化中...")

    data = load_rules()
    if not data:
        print("JSONファイルを確認してください。")
        time.sleep(10)
        return

    input_path = os.path.join(BASE_DIR, INPUT_TEXT_FILE)
    audio_dir = os.path.join(BASE_DIR, AUDIO_DIR_NAME)
    
    # 初期化：各種ファイルをリセット
    write_file(OUTPUT_PATH_FILE, "")
    write_file(THINKING_FILE, "0")
    write_file(VIDEO_TRIGGER_FILE, "0")
    
    # ★履歴リストとファイルをリセット
    global yes_history_list
    yes_history_list = [] 
    update_history_files() # 空の状態で書き込み（ファイルをクリア）

    # キーボードフック
    print("\n--- ホットキー設定 ---")
    for key_trigger, (text, wav) in KEY_MAPPINGS.items():
        keyboard.add_hotkey(key_trigger, lambda t=text, w=wav: manual_reaction_trigger(t, w))
        print(f"[{key_trigger}] -> 音声:{wav} (メモ:{text})")
    print("----------------------\n")

    last_time = 0.0
    if os.path.exists(input_path):
        last_time = os.path.getmtime(input_path)

    print("準備完了。ゲームを開始してください。")
    print(f"Yes履歴は {MAX_HISTORY_LINES} 行を超えると右列ファイルへ移動します。")

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
                if text in IGNORE_TEXTS: continue

                print(f"\n[質問検知] {text}")

                write_file(THINKING_FILE, "1")
                time.sleep(1.5)

                wav = find_response(text, data)
                
                if wav:
                    full_path = os.path.normpath(os.path.join(audio_dir, wav))
                    print(f"[回答指示] {wav}")
                    
                    # ★Yes系なら履歴に追加してファイル更新
                    if wav in POSITIVE_WAVS:
                        update_history_files(text)
                    
                    if wav == "correct.wav":
                        print("★正解！")
                        write_file(VIDEO_TRIGGER_FILE, "1")
                    
                    write_file(OUTPUT_PATH_FILE, full_path)
                
                write_file(THINKING_FILE, "0")
                time.sleep(1.0)
                write_file(OUTPUT_PATH_FILE, "")
                write_file(VIDEO_TRIGGER_FILE, "0")

    except KeyboardInterrupt:
        print("\nシステムを終了します。")
        write_file(THINKING_FILE, "0")
        write_file(VIDEO_TRIGGER_FILE, "0")

if __name__ == "__main__":
    main()