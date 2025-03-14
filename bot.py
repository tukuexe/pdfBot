import os
import time
import img2pdf
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message

# Load API credentials from GitHub Secrets (or manually if testing locally)
API_ID = int(os.getenv("API_ID", "22123890"))  # Change to your API_ID
API_HASH = os.getenv("API_HASH", "5947ed8217cb116fd2e7d0a000b14df2")  # Change to your API_HASH
BOT_TOKEN = os.getenv("BOT_TOKEN", "7573622801:AAEmhDe2I_nrwe3DFN2d_II9WaAY8xp59rE")  # Change to your BOT_TOKEN

# Create a bot client
bot = Client("pdf_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Store user messages temporarily
user_data = {}

@bot.on_message(filters.private & ~filters.command(["start", "help"]))
async def collect_messages(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Initialize user session if not exists
    if user_id not in user_data:
        user_data[user_id] = {"text": [], "images": []}

    # Store text messages
    if message.text:
        user_data[user_id]["text"].append(message.text)

    # Store image messages
    if message.photo:
        photo = await client.download_media(message.photo.file_id)
        user_data[user_id]["images"].append(photo)

    # Wait for more messages (10 seconds)
    time.sleep(10)

    # Process and send PDF
    await generate_pdf(client, chat_id, user_id)

async def generate_pdf(client, chat_id, user_id):
    if user_id not in user_data:
        return

    pdf_name = f"{user_id}_document.pdf"
    text_content = user_data[user_id]["text"]
    image_files = user_data[user_id]["images"]

    # Create PDF
    if text_content or image_files:
        try:
            if image_files:
                # Convert images to PDF (scrolling format)
                with open(pdf_name, "wb") as f:
                    f.write(img2pdf.convert(image_files))

            if text_content:
                # Add text to PDF (convert text to an image then merge)
                text_img = Image.new("RGB", (600, 800), "white")
                text_draw = Image.new("RGB", (600, 800), "white")
                text_img.save("text_page.jpg")
                image_files.insert(0, "text_page.jpg")

                with open(pdf_name, "wb") as f:
                    f.write(img2pdf.convert(image_files))

            # Send PDF to user
            await client.send_document(chat_id, pdf_name, caption="Here is your PDF 📄")

        except Exception as e:
            await client.send_message(chat_id, f"❌ Error: {str(e)}")

    # Clean up
    for img in image_files:
        os.remove(img)
    if os.path.exists(pdf_name):
        os.remove(pdf_name)

    # Reset user data
    user_data.pop(user_id, None)

# Start the bot
bot.run()
