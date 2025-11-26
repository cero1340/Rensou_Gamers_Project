import string

def normalize_text(text: str) -> str:
    """
    Whisperの出力とJSONキーを比較するために、文字列を正規化する。
    小文字化、不要な空白除去、句読点除去を行う。
    """
    # 1. 小文字化 (大文字・小文字の揺れを吸収)
    normalized_text = text.lower()
    
    # 2. 句読点の除去 (マッチングの厳しさを緩和)
    # 英語の句読点と日本語の記号を除去対象とする
    punctuation_to_remove = string.punctuation
    japanese_punctuation = '。、？！「」（）' 
    
    # 除去対象の文字を空文字に置き換えるための翻訳テーブルを作成
    translator = str.maketrans('', '', punctuation_to_remove + japanese_punctuation)
    normalized_text = normalized_text.translate(translator)
    
    # 3. 前後の空白除去
    normalized_text = normalized_text.strip()
    
    # 4. 連続する空白を一つにまとめる ('  ' -> ' ')
    normalized_text = ' '.join(normalized_text.split())

    return normalized_text