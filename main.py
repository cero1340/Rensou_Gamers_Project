import json
import os
import time
import re
import threading
import keyboard

# === 設定エリア ===
JSON_FILE_NAME = "microwave_data.json"
BASE_DIR = r"D:\Rensou_Gamers_Project"

INPUT_TEXT_FILE = "current_question.txt"
OUTPUT_PATH_FILE = "next_wav_path.txt"
THINKING_FILE = "thinking_state.txt"
VIDEO_TRIGGER_FILE = "video_trigger.txt"
TEMPLATE_FILE = "suggested_templates.txt"

HISTORY_FILE_LEFT = "yes_history_left.txt"
HISTORY_FILE_RIGHT = "yes_history_right.txt"
MAX_HISTORY_LINES = 20

AUDIO_DIR_NAME = "audio"
DEFAULT_WAV = "none.wav"

# 状態管理
yes_history_list = []
is_reacting = False
# ★質問の選択位置 (0〜7)
current_selection_index = 0

# 固定の質問リスト
QUESTIONS = [
    "1. 場所: \"Can you find it...?\"",
    "2. 素材: \"Is it made of... ?\"",
    "3. 大きさ: \"Is it bigger than... ?\"",
    "4. 色: \"Is it... ?\"",
    "5. 形: \"Is it like a... ?\"",
    "6. 動力: \"Does it use... ?\"",
    "7. 特徴: \"Does it have... ?\"",
    "8. 用途: \"Do you use it... ?\""
]

POSITIVE_WAVS = [
    "yes.wav", "strong_yes.wav", "dasai_strong_yes.wav", "amazing_question_yes.wav",
    "triple_yes.wav", "yes_ofcourse.wav", "si.wav", "usually_yes.wav",
    "some_are_yes.wav", "some_are_yes_1.wav", "some_are_yes_2.wav", "some_are_yes_3.wav",
    "some_people_use.wav", "some_people_can_find.wav", "big_partial_yes.wav",
    "partial_yes.wav", "correct.wav"
]

KEY_MAPPINGS = {
    "num 1": ("そうだべ！", "soudabe.wav"),
    "num 2": ("たしかに", "usually_yes.wav"),
    "num 3": ("なるほど！", "strong_yes.wav"),
    "num 4": ("うーん...", "depends.wav"),
    "num 5": ("ちがうよ", "no.wav"),
    "num 0": ("正解！！", "correct.wav")
}

IGNORE_TEXTS = ["考え中...", ""]

def write_file(filename, content):
    try:
        path = os.path.join(BASE_DIR, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"書き込みエラー: {e}")

# ★インジケーター（>）付きのテキスト書き出し（タイトルと区切り線を削除）
def update_selection_display():
    global current_selection_index
    display_text = "" # タイトルと区切り線を削除し、空から開始
    
    for i, q in enumerate(QUESTIONS):
        if i == current_selection_index:
            # 選択中の行の頭に > を付ける
            display_text += f"> {q}\n"
        else:
            # 選択中ではない行には半角スペースを入れて位置を揃える
            display_text += f"  {q}\n"
            
    write_file(TEMPLATE_FILE, display_text)
    print(f"[位置変更] {current_selection_index + 1}番")

# 操作キー用の関数
def next_selection():
    global current_selection_index
    current_selection_index = (current_selection_index + 1) % len(QUESTIONS)
    update_selection_display()

def prev_selection():
    global current_selection_index
    current_selection_index = (current_selection_index - 1) % len(QUESTIONS)
    update_selection_display()

def update_history_files(new_text=None):
    global yes_history_list
    if new_text:
        yes_history_list.append(f"・{new_text}")
    left_content_list = yes_history_list[:MAX_HISTORY_LINES]
    right_content_list = yes_history_list[MAX_HISTORY_LINES:]
    write_file(HISTORY_FILE_LEFT, "\n".join(left_content_list))
    write_file(HISTORY_FILE_RIGHT, "\n".join(right_content_list))

def load_json(filename):
    try:
        path = os.path.join(BASE_DIR, filename)
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"★JSON読み込み失敗({filename}): {e}")
        return None

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
            wav_file = data.get("response_map", {}).get(v)
            if wav_file: return wav_file
            if v.endswith(".wav"): return v
            return DEFAULT_WAV
    return DEFAULT_WAV

def manual_reaction_trigger(log_text, wav_name):
    global is_reacting
    if is_reacting: return 
    is_reacting = True
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
    finally:
        is_reacting = False

def main():
    print("=== AI回答システム Ver 3.1 (シンプルリスト版) ===")

    data = load_json(JSON_FILE_NAME)
    if not data:
        print("JSONファイルを確認してください。")
        return

    # 初回起動時にテキストを書き出し
    update_selection_display()

    print("\n--- 操作キー ---")
    keyboard.add_hotkey("ctrl+up", prev_selection)
    keyboard.add_hotkey("ctrl+down", next_selection)
    print("[Ctrl + ↑] 上の項目へ / [Ctrl + ↓] 下の項目へ")

    for key_trigger, (text, wav) in KEY_MAPPINGS.items():
        keyboard.add_hotkey(key_trigger, lambda t=text, w=wav: manual_reaction_trigger(t, w))
    
    input_path = os.path.join(BASE_DIR, INPUT_TEXT_FILE)
    audio_dir = os.path.join(BASE_DIR, AUDIO_DIR_NAME)
    
    write_file(OUTPUT_PATH_FILE, "")
    write_file(THINKING_FILE, "0")
    write_file(VIDEO_TRIGGER_FILE, "0")
    update_history_files()

    last_time = os.path.getmtime(input_path) if os.path.exists(input_path) else 0.0

    print("\n準備完了。")

    try:
        while True:
            time.sleep(0.1)
            if not os.path.exists(input_path): continue
            try:
                mtime = os.path.getmtime(input_path)
            except: continue

            if mtime > last_time:
                last_time = mtime
                time.sleep(0.1) 
                try:
                    with open(input_path, 'r', encoding='utf-8') as f:
                        text = f.read().strip()
                except: continue

                if not text or text in IGNORE_TEXTS: continue

                print(f"\n[質問検知] {text}")
                write_file(THINKING_FILE, "1")
                time.sleep(1.5)
                wav = find_response(text, data)
                if wav:
                    full_path = os.path.normpath(os.path.join(audio_dir, wav))
                    if wav in POSITIVE_WAVS:
                        update_history_files(text)
                    if wav == "correct.wav":
                        write_file(VIDEO_TRIGGER_FILE, "1")
                    write_file(OUTPUT_PATH_FILE, full_path)
                
                write_file(THINKING_FILE, "0")
                time.sleep(1.0)
                write_file(OUTPUT_PATH_FILE, "")
                write_file(VIDEO_TRIGGER_FILE, "0")

    except KeyboardInterrupt:
        print("\n終了します。")

if __name__ == "__main__":
    main()