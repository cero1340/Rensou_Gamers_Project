import json
import os
import time
import keyboard

# === 設定エリア ===
JSON_FILE_NAME = "microwave_data.json"
BASE_DIR = r"D:\Rensou_Gamers_Project"

INPUT_TEXT_FILE = "current_question.txt"
OUTPUT_PATH_FILE = "next_wav_path.txt"
THINKING_FILE = "thinking_state.txt"
AUDIO_DIR_NAME = "audio"
DEFAULT_WAV = "again.wav"
PAUSE_HOTKEY = "f9"

is_paused = False

def write_file(filename, content):
    try:
        path = os.path.join(BASE_DIR, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    except:
        pass

def toggle_pause(e):
    global is_paused
    is_paused = not is_paused
    if is_paused:
        print(f"\n[一時停止] LocalVocal OFF (解除: {PAUSE_HOTKEY})")
        write_file(THINKING_FILE, "2") # 2 = 完全停止
    else:
        print(f"\n[再開] LocalVocal ON")
        write_file(THINKING_FILE, "0") # 0 = 待機

def load_rules():
    try:
        with open(os.path.join(BASE_DIR, JSON_FILE_NAME), 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def find_response(text, data):
    text = text.lower()
    rules = []
    for cat, items in data.get("rules", {}).items():
        for k, v in items.items():
            rules.append((k.lower(), v))
    rules.sort(key=lambda x: len(x[0]), reverse=True)
    
    for k, v in rules:
        if k in text:
            print(f"ヒット: {k} -> {v}")
            return data.get("response_map", {}).get(v)
    return DEFAULT_WAV

def main():
    print("=== システム起動（フィルタ制御あり） ===")
    keyboard.on_press_key(PAUSE_HOTKEY, toggle_pause)
    data = load_rules()
    if not data: return

    input_path = os.path.join(BASE_DIR, INPUT_TEXT_FILE)
    last_time = 0
    audio_dir = os.path.join(BASE_DIR, AUDIO_DIR_NAME)

    write_file(OUTPUT_PATH_FILE, "")
    write_file(THINKING_FILE, "0")
    
    if os.path.exists(input_path):
        last_time = os.path.getmtime(input_path)

    try:
        while True:
            time.sleep(0.5)
            if is_paused: continue # 一時停止中は監視しない

            if not os.path.exists(input_path): continue
            mtime = os.path.getmtime(input_path)

            if mtime > last_time:
                last_time = mtime
                time.sleep(0.1)
                
                try:
                    with open(input_path, 'r', encoding='utf-8') as f:
                        text = f.read().strip()
                except:
                    continue

                if not text: continue
                print(f"\n質問: {text}")

                # 1. 考え中ON (文字表示 & フィルタOFF)
                write_file(THINKING_FILE, "1")
                print("考え中... (フィルタ停止)")

                time.sleep(1.5)

                wav = find_response(text, data)
                if wav:
                    full_path = os.path.normpath(os.path.join(audio_dir, wav))
                    write_file(OUTPUT_PATH_FILE, full_path)
                    print(f"回答: {wav}")

                # 2. 考え中OFF (文字非表示 & フィルタON)
                write_file(THINKING_FILE, "0")

                time.sleep(1.0)
                write_file(OUTPUT_PATH_FILE, "") 

    except KeyboardInterrupt:
        print("終了")

if __name__ == "__main__":
    main()