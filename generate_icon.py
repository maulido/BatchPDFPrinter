from PIL import Image, ImageDraw

def create_icon():
    # Create a transparent image 256x256
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Outer blue rounded rectangle
    # Light blue color: #1f6aa5 (CustomTkinter default blue) or #1ca3ec
    blue_color = (28, 163, 236, 255) 
    
    # Coordinates for outer box
    margin = 20
    outer_box = [margin, margin, size-margin, size-margin]
    draw.rounded_rectangle(outer_box, radius=40, fill=blue_color)
    
    # Inner dark rounded rectangle (hole)
    inner_margin = 65
    inner_box = [inner_margin, inner_margin, size-inner_margin, size-inner_margin]
    dark_color = (36, 36, 36, 255) # Dark gray background
    draw.rounded_rectangle(inner_box, radius=20, fill=dark_color)
    
    # Save as .ico
    img.save('icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
    print("icon.ico generated successfully!")

if __name__ == "__main__":
    create_icon()
