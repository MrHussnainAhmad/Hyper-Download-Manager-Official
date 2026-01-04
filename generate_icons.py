import sys
import os
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

def generate_icons():
    app = QApplication(sys.argv)
    
    source = "d:/FDM/icon.png"
    if not os.path.exists(source):
        print("Source icon.png not found!")
        return

    sizes = [16, 32, 48, 128]
    output_dir = "d:/FDM/extension/icons"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    img = QImage(source)
    if img.isNull():
        print("Failed to load icon.png")
        return

    for size in sizes:
        scaled = img.scaled(size, size)
        out_path = os.path.join(output_dir, f"icon{size}.png")
        scaled.save(out_path)
        print(f"Generated {out_path}")

if __name__ == "__main__":
    generate_icons()
