import os
from PIL import Image, ImageDraw

def create_logo():
    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded background
    bg_color = (13, 17, 26, 255)
    margin = 20
    draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=90, fill=bg_color, outline=(139, 92, 246, 255), width=8)

    # Inner subtle glow ring
    draw.rounded_rectangle([margin + 12, margin + 12, size - margin - 12, size - margin - 12], radius=80, fill=None, outline=(109, 40, 217, 80), width=4)

    violet = (139, 92, 246, 255)
    violet_bright = (167, 139, 250, 255)
    emerald = (16, 185, 129, 255)
    cyan = (6, 182, 212, 255)

    # Isometric 3D Project Cube Stack
    # Top face
    draw.polygon([(256, 130), (380, 200), (256, 270), (132, 200)], fill=(45, 35, 75, 255), outline=violet_bright, width=6)

    # Left face
    draw.polygon([(132, 200), (256, 270), (256, 390), (132, 320)], fill=(30, 25, 55, 255), outline=violet, width=6)

    # Right face
    draw.polygon([(256, 270), (380, 200), (380, 320), (256, 390)], fill=(20, 15, 40, 255), outline=violet, width=6)

    # Glowing Green Checkmark on top face (Completion indicator)
    draw.line([(210, 195), (245, 230)], fill=emerald, width=9)
    draw.line([(245, 230), (310, 160)], fill=emerald, width=9)

    # Code brackets inside left face
    draw.line([(180, 250), (165, 265), (180, 280)], fill=cyan, width=5)
    draw.line([(210, 250), (225, 265), (210, 280)], fill=cyan, width=5)

    assets_dir = r"C:\Users\admin\Desktop\VS Codes\Projects\ProjectVault\assets"
    png_path = os.path.join(assets_dir, "logo.png")
    ico_path = os.path.join(assets_dir, "app_icon.ico")
    
    img.save(png_path, "PNG")
    print(f"Saved logo: {png_path}")

    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(ico_path, format="ICO", sizes=icon_sizes)
    print(f"Saved icon: {ico_path}")

if __name__ == "__main__":
    create_logo()
