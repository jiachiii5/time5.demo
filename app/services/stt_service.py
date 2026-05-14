import time
import random

def transcribe_audio(audio_path):
    """
    Mock Service: Simulate sending audio to STT API.
    Returns transcribed text.
    """
    # 模擬 API 延遲
    time.sleep(2)
    
    # 針對這個 MVP，隨機回傳一些預設的文字
    mock_texts = [
        "這是一段關於海洋與星空的聲音，感受到海風的吹拂，繁星點點灑落在大海上。",
        "我在城市的角落聽到雨聲，一盞橘黃色的路燈下，有人正撐著傘慢慢走過。",
        "咖啡廳裡人聲鼎沸，但爵士樂的聲音還是很清晰，給人一種溫暖放鬆的感覺。",
        "在森林深處，鳥鳴和微風吹過樹葉的沙沙聲，彷彿時間靜止了。"
    ]
    
    return random.choice(mock_texts)
