import time
import random

def generate_image(prompt, style="寫實"):
    """
    Mock Service: Simulate sending prompt to Image Generation API.
    Returns image URL or local path.
    """
    # 模擬 API 延遲
    time.sleep(3)
    
    # 為了 MVP，我們先使用 Unsplash 的隨機圖片來當作生成的圖片
    # 實際上這裡應該回傳 AI 生成的圖片並儲存到 static/uploads/
    # 我們根據 prompt 的長度或內容隨機挑一張圖片
    
    random_id = random.randint(1, 1000)
    image_url = f"https://picsum.photos/seed/{random_id}/800/600"
    
    return image_url
