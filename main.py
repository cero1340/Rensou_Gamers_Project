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
    """
    質問テキストとJSONルールを照合し、回答WAVファイル名を決定する
    """
    # 質問テキストを前処理：小文字化し、句読点をスペースに置換
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text) 
    text = re.sub(r'\s+', ' ', text).strip()
    
    rules = []
    
    # 1. JSONの新しいカテゴリ構造を展開してリスト化
    # (キーワード, 回答キー, カテゴリ名) のタプルリストを作成
    for cat, items in data.get("rules", {}).items():
        for k, v in items.items():
            # ★修正: category_answer の特別扱い(EXACT)を廃止し、すべて部分一致で判定
            # これにより "It is a microwave" という文章でも正解判定が出るようになる
            rules.append((k.lower(), v, cat))
    
    # 2. 長いキーワード順に並べ替え（誤爆防止の最長一致検索を優先）
    # (カテゴリ名が'EXACT'なルールは、長さに関わらず最初（完全一致）で処理するため、ここで優先的に並べる必要はないが、部分一致の優先度を上げるために実行)
    rules.sort(key=lambda x: len(x[0]), reverse=True)
    
    for k, v, cat in rules:
        
        # 3. 判定ロジックをシンプルに一本化 (すべて部分一致)
        # 修正: "microwave" が "it is a microwave" に含まれていればOK
        if k in text:
            print(f"ヒットしました: [{cat}] '{k}' -> Key: '{v}'")
            
            # 5. 回答キーからWAVファイル名を確定
            
            # 5-1. response_map からファイル名を探す
            wav_file = data.get("response_map", {}).get(v)
            
            # 5-2. 見つかればそれを返す
            if wav_file:
                return wav_file
            
            # 5-3. 見つからない場合、JSONに直接ファイル名が書かれている可能性をケア（予備的なロジック）
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
    write_file(OUTPUT_PATH_FILE, "") # 回答ファイルパスをクリア
    write_file(THINKING_FILE, "0") # 考え中ステータスを待機中に設定 (Lua連携)
    write_file(VIDEO_TRIGGER_FILE, "0") # ★追加: 動画トリガーを初期化
    
    last_time = 0.0 # float型で初期化
    if os.path.exists(input_path):
        last_time = os.path.getmtime(input_path)

    print("準備完了。OBSのF9ホットキーを押して、ゲームを開始してください。")

    try:
        while True:
            # 0.1秒ごとにファイルをチェック
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
                # LocalVocalの書き込み完了を待つために少し待機
                time.sleep(0.1) 
                
                try:
                    with open(input_path, 'r', encoding='utf-8') as f:
                        text = f.read().strip()
                except:
                    continue

                if not text: continue
                
                print(f"\n[質問検知] {text}")

                # 1. OBSに「考え中」を表示させる (Lua連携)
                write_file(THINKING_FILE, "1")
                
                # 演出：1.5秒待つ（AIが考えているフリ）
                time.sleep(1.5)

                # 2. 回答を決める
                wav = find_response(text, data)
                
                if wav:
                    # WAVファイルのフルパスを作成
                    full_path = os.path.normpath(os.path.join(audio_dir, wav))
                    print(f"[回答指示] {wav}")
                    
                    # ★追加: もし正解(correct.wav)なら、動画再生フラグを立てる
                    # (JSONの設定に合わせてwavファイル名で判定)
                    if wav == "correct.wav":
                        print("★正解を検知！動画再生指示を送ります。")
                        write_file(VIDEO_TRIGGER_FILE, "1")
                    
                    # 3. OBSにWAVパスを渡す（これで音が鳴る）
                    write_file(OUTPUT_PATH_FILE, full_path)
                
                # 4. OBSの「考え中」を消す (Lua連携)
                write_file(THINKING_FILE, "0")

                # 次の処理のために指示ファイルを空にしておく
                # Luaでの再生完了を待たず、すぐに空にするロジック
                time.sleep(1.0)
                write_file(OUTPUT_PATH_FILE, "")
                write_file(VIDEO_TRIGGER_FILE, "0") # ★追加: 動画トリガーを戻す

    except KeyboardInterrupt:
        print("\nシステムを終了します。")
        # 終了時には状態をクリア（待機中）
        write_file(THINKING_FILE, "0")
        write_file(VIDEO_TRIGGER_FILE, "0")

if __name__ == "__main__":
    main()