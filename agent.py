import os
import base64
import datetime
import shutil
import glob
from openai import OpenAI

# 1. Setup Client (GitHub Models / OpenAI compatible)
client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=os.environ.get("GITHUB_TOKEN")
)

def process_images():
    print("--- Starting AI Agent ---")
    
    # 2. Ensure Folders Exist
    # This creates the directories if they are missing
    os.makedirs("posts", exist_ok=True)
    os.makedirs("images/processed", exist_ok=True)
    
    # 3. List all files in 'images' for debugging
    if os.path.exists("images"):
        print(f"Directory 'images' content: {os.listdir('images')}")
    else:
        print("ERROR: 'images' directory does not exist!")
        return

    # 4. Search for new images (Case-Insensitive)
    # We look for files in 'images/' but NOT in 'images/processed/'
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
    image_files = []
    for ext in extensions:
        # glob.glob finds files matching the pattern
        found = glob.glob(os.path.join("images", ext))
        image_files.extend(found)

    # Filter out anything that is already inside the processed folder
    image_files = [f for f in image_files if "processed" not in f]

    if not image_files:
        print("No new images found to process. Exiting.")
        return

    print(f"Found {len(image_files)} image(s) to process.")

    for img_path in image_files:
        print(f"Processing image: {img_path}")
        
        try:
            # Generate a clean timestamp for filenames
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y%m%d-%H%M%S")
            
            # Get the original file extension (e.g., .jpg)
            file_ext = os.path.splitext(img_path)[1]
            new_image_name = f"photo-{timestamp}{file_ext}"
            new_image_path = os.path.join("images/processed", new_image_name)

            # 5. Read and Encode Image to Base64
            with open(img_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

            # 6. Call AI Model
            print(f"Requesting AI description for {img_path}...")
            response = client.chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Create a beautiful blog post in Markdown format. Start with a # Title, then write 2-3 engaging paragraphs about the scene. Use a poetic and professional tone."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_string}"}}
                    ]
                }],
                model="gpt-4o-mini"
            )

            blog_content = response.choices[0].message.content
            if not blog_content:
                print(f"Warning: AI returned empty content for {img_path}")
                continue

            # 7. Create the Markdown File
            # Note: The path to the image in the MD file must be relative to the /posts/ folder
            md_filename = f"post-{timestamp}.md"
            md_path = os.path.join("posts", md_filename)
            
            with open(md_path, "w", encoding="utf-8") as md_file:
                # We tell the Markdown to look inside images/processed/
                md_file.write(f"![{new_image_name}](../images/processed/{new_image_name})\n\n")
                md_file.write(blog_content)

            # 8. Move the original image to the processed folder
            shutil.move(img_path, new_image_path)
            
            print(f"✅ Success: Created {md_path}")
            print(f"✅ Moved: {img_path} -> {new_image_path}")

        except Exception as e:
            print(f"❌ Error processing {img_path}: {str(e)}")

    print("--- AI Agent Finished ---")

if __name__ == "__main__":
    process_images()
