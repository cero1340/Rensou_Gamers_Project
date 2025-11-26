import json
import os
import time

# === 設定エリア ===
JSON_FILE_NAME = "microwave_data.json"
BASE_DIR = r"D:\Rensou_Gamers_Project"

INPUT_TEXT_FILE = "current_question.txt"
OUTPUT_PATH_FILE = "next_wav_path.txt"
THINKING_FILE = "thinking_state.txt"
AUDIO_DIR_NAME = "audio"
DEFAULT_WAV = "none.wav"

# ファイル書き込み関数
def write_file(filename, content):
    try:
        path = os.path.join(BASE_DIR, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"書き込みエラー: {e}")

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
    rules = []
    
    # JSONの構造を展開してリスト化
    for cat, items in data.get("rules", {}).items():
        for k, v in items.items():
            rules.append((k.lower(), v))
    
    # 長いキーワード順に並べ替え（誤爆防止）
    rules.sort(key=lambda x: len(x[0]), reverse=True)
    
    for k, v in rules:
        if k in text:
            print(f"ヒットしました: '{k}' -> Key: '{v}'")
            
            # 1. response_map からファイル名を探す
            wav_file = data.get("response_map", {}).get(v)
            
            # 2. 見つかればそれを返す
            if wav_file:
                return wav_file
            
            # 3. 見つからない場合、JSONに直接ファイル名が書かれている可能性をケア
            if v.endswith(".wav"):
                return v
            
            print(f"★警告: Key '{v}' に対応するWAVファイルが response_map にありません。")
            return DEFAULT_WAV
            
    print("ヒットするキーワードがありませんでした。")
    return DEFAULT_WAV

def main():
    print("=== AI回答システム Ver 1.2 (常時監視モード) ===")
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
    
    last_time = 0
    if os.path.exists(input_path):
        last_time = os.path.getmtime(input_path)

    print("準備完了。F9を押して話しかけてください。")

    try:
        while True:
            # 0.1秒ごとにファイルをチェック（負荷はほぼゼロ）
            time.sleep(0.1)

            if not os.path.exists(input_path):
                continue

            # ファイルの更新日時をチェック
            try:
                mtime = os.path.getmtime(input_path)
            except:
                continue

            # 更新があった場合のみ処理
            if mtime > last_time:
                last_time = mtime
                time.sleep(0.1) # 書き込み完了待ち
                
                try:
                    with open(input_path, 'r', encoding='utf-8') as f:
                        text = f.read().strip()
                except:
                    continue

                if not text: continue
                
                print(f"\n[質問検知] {text}")

                # 1. OBSに「考え中」を表示させる
                write_file(THINKING_FILE, "1")
                
                # 演出：1.5秒待つ（AIが考えているフリ）
                time.sleep(1.5)

                # 2. 回答を決める
                wav = find_response(text, data)
                
                if wav:
                    full_path = os.path.normpath(os.path.join(audio_dir, wav))
                    print(f"[回答指示] {wav}")
                    # 3. OBSにWAVパスを渡す（これで音が鳴る）
                    write_file(OUTPUT_PATH_FILE, full_path)
                
                # 4. OBSの「考え中」を消す
                write_file(THINKING_FILE, "0")

                # 次のために指示ファイルを空にしておく
                time.sleep(1.0)
                write_file(OUTPUT_PATH_FILE, "") 

    except KeyboardInterrupt:
        print("\n終了します。")

if __name__ == "__main__":
    main()