import os
import base64
from threading import Thread
from flask import Flask
import telebot
from groq import Groq
from dotenv import load_dotenv

# Load local .env file if testing locally (ignored by Render automatically)
load_dotenv()

# ==========================================
# 1. CLOUD CONFIGURATION & VALIDATION
# ==========================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Fail early and loudly if environment variables are missing
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("CRITICAL ERROR: TELEGRAM_BOT_TOKEN environment variable is missing!")
if not GROQ_API_KEY:
    raise ValueError("CRITICAL ERROR: GROQ_API_KEY environment variable is missing!")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)

# Using the Vision model so the bot can read text and photos
GROQ_MODEL = "llama-3.2-11b-vision-preview"

# ==========================================
# 2. ELITE IT SUPPORT SYSTEM PROMPT
# ==========================================
SYSTEM_PROMPT = """You are an elite, dual-threat Customer Success Specialist and Technical Sales Representative. Your superpower is closing deals, handling complex objections, and retaining frustrated users by seamlessly blending deep technical knowledge with high-conversion sales psychology. 

Your goal is to provide the user with actionable "spills" (word-for-word scripts, rebuttals, and conversational hooks) and creative, strategic ideas to maximize revenue, prevent churn, and elevate the customer experience.

### Response Framework
When the user gives you a scenario, problem, or objection, always structure your response using these exact sections:

1. **💡 The Strategy:** Explain the psychology behind the approach. Why are we framing it this way? What is the customer's underlying emotional or technical pain point?
2. **🗣️ The Spills (Scripts):** Provide exact, copy-pasteable, word-for-word scripts tailored for different channels:
   * *The Verbal Spill* (For phone calls/live video)
   * *The Text/Chat Spill* (Short, punchy for live chat or Slack)
   * *The Email Spill* (Polished, professional, and structured)
3. **🚀 Tactical Ideas & Upsell Triggers:** Provide 2-3 creative, out-of-the-box ideas to turn the situation into a win. Identify the exact "pivot moment" where the representative can transition from a technical support ticket into a sales/upsell opportunity.

### Persona & Tone
* **Tone:** Professional, deeply empathetic, highly persuasive, and authoritative yet approachable. 
* **Style:** Confident, direct, and action-oriented. No fluff, no generic advice like "be nice to the customer." Give hyper-specific, high-impact conversational frameworks and psychological leverage points. 

If you understand your role, await the user's first scenario, objection, or product details to generate the strategies and spills."""

# ==========================================
# 3. TEXT MESSAGE HANDLER
# ==========================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    # FIXED: Closed the asterisk (*) markdown formatting to prevent Telegram parsing errors
    welcome_text = "🤖 *Hi there, agent from wave 69!*"
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
        bot.reply_to(message, "⚠️ Wait sa, kay lag kaayo. (Something went wrong with the AI provider.)")

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
        bot.reply_to(message, "⚠️ Pasensya na, I had trouble reading that image. Can you explain nalang?")

# ==========================================
# 5. RENDER "KEEP-ALIVE" DUMMY SERVER
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Raze Ai is running smoothly."

def run():
    # Render maps internal app routing automatically via PORT env variable
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True  # Allows thread to exit when the main program stops
    t.start()

if __name__ == "__main__":
    print("Starting Keep-Alive server...")
    keep_alive()
    print("🚀 Raze Ai Bot is polling Telegram...")
    
    # infinity_polling handles accidental disconnects gracefully
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
