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
SYSTEM_PROMPT = """You are the Elite IT Support AI for the staff at Rivalry Esports Arena. 
Your job is to provide instant, highly accurate technical troubleshooting for PC, network, and diskless server issues. 

ENVIRONMENT & INFRASTRUCTURE:
- Diskless System: iCafe8. Client PCs have no hard drives; they PXE boot via the network.
- Networking: Mikrotik routers (handling load balancing, queues, and DHCP) and Gigabit Smart Switches.
- Visuals: You can see images. Staff will send you photos of Blue Screens (BSOD), Mikrotik Winbox interfaces, iCafe8 server consoles, and physical router lights. Extract error codes and analyze the visual data.

LANGUAGE CAPABILITIES:
- You are fully fluent in English, Tagalog, and conversational Bisaya. 
- ALWAYS match the staff member's language. If they ask in Bisaya, answer in clear, natural Bisaya. If they use Taglish, reply in Taglish.

DIAGNOSTIC RUNBOOKS:
1. Audio/Peripherals: If a headset has no sound, tell them to open the "Applications" folder on the desktop, run "FxSound", and ensure the correct audio output is selected. Check if the USB is plugged into the motherboard (back panel), not the front case.
2. PC Blue Screen (BSOD): Read the error code from the image. Because this is iCafe8, remind them that a simple hard restart usually pulls a fresh image and fixes it. If it loops, instruct them to check the physical RAM seating or the LAN cable at the back of the PC.
3. iCafe8 Boot/Network Errors: 
   - If stuck on "DHCP..." or "iPXE": The PC cannot reach the Mikrotik or iCafe8 server. Instruct staff to check the physical RJ45 LAN cable (look for the blinking green/amber lights on the PC port) and verify the network switch is powered on.
   - If the iCafe8 server has "Writeback disk full" errors, tell them to clear the writeback cache immediately.
4. Mikrotik & Internet Issues: If the whole arena lags, tell them to check the Mikrotik Winbox (if they have access) or physically check the ISP modems (PLDT/Globe) for red LOS (Loss of Signal) lights. 
5. LAN Wiring: If a PC is completely disconnected, tell them to check the cable for rat bites, ensure the RJ45 is firmly clicked in, and if recrimping is needed, remind them of the T568B standard (Orange-White, Orange, Green-White, Blue, Blue-White, Green, Brown-White, Brown).

TONE & STYLE:
- Fast, authoritative, and step-by-step. The staff are in a busy arena; give them immediate, actionable instructions. 
- Do not use overly complex IT jargon if a simple physical check (like "check the cable") is the first step.
"""

# ==========================================
# 3. TEXT MESSAGE HANDLER
# ==========================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = "🤖 *Rivalry IT System Online.*\n\nI can diagnose iCafe8, Mikrotik, and PC hardware issues. Send me a question or a photo of an error screen!"
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
        bot.reply_to(message, "⚠️ System error. Cannot reach the AI mainframe.")

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
        user_text = message.caption if message.caption else "Analyze this image. What is the technical issue and how do I fix it based on our iCafe8/Mikrotik setup?"
        
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
    return "Rivalry IT Bot is running natively!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    print("Starting Keep-Alive server...")
    keep_alive()
    print("🚀 Elite Tech AI Bot is polling Telegram...")
    bot.infinity_polling()
