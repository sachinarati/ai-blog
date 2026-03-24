import os
import base64
import datetime
import shutil
import glob
from openai import OpenAI

# 1. Setup client for GitHub Models (2026 Endpoint)
client = OpenAI(
    base_url="https://models.github.ai/inference",
    api_key=os.environ.get("GITHUB_TOKEN")
)

def generate_blog():
    os.makedirs("posts", exist_ok=True)
    os.makedirs("images", exist_ok=True)
    
    input_path = "images/input.jpg"
    if not os.path.exists(input_path):
        print("⏸️ No input.jpg found. Skipping...")
        return

    # 2. CLEANUP: Delete all archived photos to keep the repo clean
    old_photos = glob.glob("images/photo-*.jpg")
    for photo in old_photos:
        os.remove(photo)
        print(f"🗑️ Cleaned up: {photo}")

    # 3. ARCHIVE: Create a unique name for the new post
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    unique_img = f"photo-{timestamp}.jpg"
    shutil.copy(input_path, f"images/{unique_img}")

    # 4. AI ANALYSIS
    with open(f"images/{unique_img}", "rb") as f:
        encoded_image = base64.b64encode(f.read()).decode("utf-8")

    print(f"🤖 Analyzing {unique_img}...")
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Write a professional blog post about this image in very detail and engaging format which will grab the user attention. Start with a # Title."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}},
                    ],
                }
            ],
            model="gpt-4o-mini"
        )

        ai_text = response.choices[0].message.content
        
        # 5. LINK IMAGE & SAVE
        # We point to the unique archived image
        img_link = f"![Blog Visual](../images/{unique_img})\n\n"
        with open(f"posts/post-{timestamp}.md", "w") as f:
            f.write(img_link + ai_text)

        # 6. DELETE INPUT: Remove the trigger file so it doesn't loop
        os.remove(input_path)
        print(f"✅ Success! Post generated and input.jpg cleared.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    generate_blog()