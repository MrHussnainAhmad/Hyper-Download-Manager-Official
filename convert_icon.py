import os

def convert():
    try:
        from PIL import Image
    except ImportError:
       print("Pillow not installed")
       return

    if not os.path.exists("icon.png"):
        print("icon.png not found!")
        return
        
    img = Image.open("icon.png")
    img.save("icon.ico", format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print("Converted icon.png to icon.ico")

if __name__ == "__main__":
    try:
        convert()
    except ImportError:
        print("Pillow not installed. Installing...")
        import subprocess
        subprocess.check_call(["python", "-m", "pip", "install", "Pillow"])
        convert()
    except Exception as e:
        print(f"Error converting icon: {e}")
