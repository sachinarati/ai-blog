import os
import base64
import datetime
import shutil
import glob
from openai import OpenAI

# Initialize OpenAI Client (GitHub Models)
client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.environ.get("GITHUB_TOKEN")
)

def process_images():
    # 1. Automatic Folder Creation
    os.makedirs("posts", exist_ok=True)
    os.makedirs("images/processed", exist_ok=True)
    
    # 2. Look for any new images in the main /images folder
    valid_extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
    all_files = []
    for ext in valid_extensions:
        all_files.extend(glob.glob(f"images/{ext}"))
    
    if not all_files:
        print("No new images found in /images to process.")
        return

    print(f"Found {len(all_files)} new image(s). Processing...")

    for img_path in all_files:
        # Skip if the path is the 'processed' folder itself
        if os.path.isdir(img_path): continue
            
        try:
            filename = os.path.basename(img_path)
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            file_extension = os.path.splitext(filename)[1]
            
            # Unique name for the permanent archive
            unique_name = f"photo-{timestamp}{file_extension}"
            
            # 3. Read and Encode image
            with open(img_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

            # 4. AI Generation
            response = client.chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Write a high-quality, engaging blog post about this image in Markdown. Use a creative title."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                    ]
                }],
                model="gpt-4o-mini"
            )

            # 5. Create Markdown File (Points to the 'processed' path)
            markdown_content = f"![Blog Image](../images/processed/{unique_name})\n\n"
            markdown_content += response.choices[0].message.content
            
            with open(f"posts/post-{timestamp}.md", "w") as f:
                f.write(markdown_content)

            # 6. MOVE the image to prevent re-processing
            dest_path = f"images/processed/{unique_name}"
            shutil.move(img_path, dest_path)
            
            print(f"✅ Successfully processed: {filename}")

        except Exception as e:
            print(f"❌ Error processing {img_path}: {e}")

if __name__ == "__main__":
    process_images()
