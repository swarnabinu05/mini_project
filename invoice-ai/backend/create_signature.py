from PIL import Image, ImageDraw, ImageFont
import os

# Create a simple signature image
def create_signature_image():
    # Create a new image with white background
    width, height = 300, 100
    image = Image.new('RGBA', (width, height), (255, 255, 255, 0))  # Transparent background
    draw = ImageDraw.Draw(image)
    
    # Draw a simple signature-like text
    try:
        # Try to use a more script-like font if available
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Draw signature text
    text = "Manager Signature"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    draw.text((x, y), text, fill=(0, 0, 139, 255), font=font)  # Dark blue color
    
    # Add a simple underline
    draw.line([(x, y + text_height + 5), (x + text_width, y + text_height + 5)], 
              fill=(0, 0, 139, 255), width=2)
    
    return image

if __name__ == "__main__":
    # Create the signature image
    signature = create_signature_image()
    
    # Save it to the assets directory
    assets_dir = "d:/minipro/invoice-ai/backend/assets"
    os.makedirs(assets_dir, exist_ok=True)
    
    signature_path = os.path.join(assets_dir, "signature.png")
    signature.save(signature_path, "PNG")
    print(f"Signature image created at: {signature_path}")
