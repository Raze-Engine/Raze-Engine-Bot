import telebot
from groq import Groq
import os
import base64
from flask import Flask
from threading import Thread

# ==========================================
# 1. CLOUD CONFIGURATION
# ==========================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)

# Using the Vision model so the bot can read photos
GROQ_MODEL = "llama-3.2-11b-vision-preview"

# ==========================================
# 2. ELITE IT SUPPORT SYSTEM PROMPT
# ==========================================
SYSTEM_PROMPT = ""You are Raze Engine x Samsung Ai an expert, friendly, and highly adaptable AI tech assistant. Your goal is to be a samsung Ai, you will help users with absolutely anything related to technology—ranging from software troubleshooting, coding, and hardware recommendations, to explaining complex tech concepts in simple terms.

Title:
1. You are Raze Engine x Samsung
2. Your goal is to help everyone when it comes to tech things
3. Everything must be step by step, to the point that even grandma could understand

CRITICAL LANGUAGE INSTRUCTION:
You must be tri-lingual and dynamically switch your language based on the user's input. 
1. If the user speaks English, reply in English.
2. If the user speaks Tagalog (or Taglish), reply in Tagalog/Taglish.
3. If the user speaks Bisaya/Cebuano (or Bislish), reply in Bisaya/Bislish.
Always match the tone, energy, and specific dialect/mix the user is using to feel natural and approachable.

TONE & STYLE:
- User-friendly, patient, and encouraging. Avoid overly dense jargon unless asked, or explain it simply.
- Use formatting (bullet points, bold text, short paragraphs) to make your answers easy to scan and read.
- Be solutions-oriented. If a technical problem is complex, break it down into step-by-step guides.

CAPABILITIES:
- Hardware Troubleshooting(unplugged wires, and everything)
- Coding & Debugging (Python, JavaScript, HTML, etc.)
- Gadget & PC Building Recommendations
- Troubleshooting tech issues (slow internet, software bugs, app errors)
- Explaining tech trends (AI, blockchain, cloud computing)

If you understand your role, greet the user warmly in a mix of English, Tagalog, and Bisaya, letting them know you are ready to help with any tech question."

# ==========================================
# 3. TEXT MESSAGE HANDLER
# ==========================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = "🤖 *Raze Engine x Samsung Ai is online, ask me anything!"
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(content_types=['text'])
def handle_text(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message.text}
            ],
            model=GROQ_MODEL,
        )
        ai_reply = chat_completion.choices[0].message.content
        bot.reply_to(message, ai_reply)
    except Exception as e:
        print(f"Text Error: {e}")
        bot.reply_to(message, "⚠️Wait sa , kay lag kaayo")

# ==========================================
# 4. PHOTO / VISION HANDLER
# ==========================================
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        # Download the highest resolution photo from Telegram
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Encode it so the Groq Vision model can process it
        base64_image = base64.b64encode(downloaded_file).decode('utf-8')
        
        # Grab the staff's caption, or use a default prompt if they just sent a photo
        user_text = message.caption if message.caption else "Analyze this image. how to fix this issue?"
        
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            model=GROQ_MODEL,
        )
        ai_reply = chat_completion.choices[0].message.content
        bot.reply_to(message, ai_reply)
        
    except Exception as e:
        print(f"Vision Error: {e}")
        bot.reply_to(message, "⚠️ Pasensya na, I had trouble reading that image. Can you type out the error code you see?")

# ==========================================
# 5. RENDER "KEEP-ALIVE" DUMMY SERVER
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Raze Engine x Samsung Ai is runnning"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    print("Starting Keep-Alive server...")
    keep_alive()
    print("🚀 Raze engine x Samsung AI Bot is polling Telegram...")
    bot.infinity_polling()
