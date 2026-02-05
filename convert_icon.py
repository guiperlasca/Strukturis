from PIL import Image
import os

try:
    img = Image.open("assets/icon.png")
    img.save("assets/icon.ico", format='ICO', sizes=[(256, 256)])
    print("Success: assets/icon.ico created")
except Exception as e:
    print(f"Error: {e}")
