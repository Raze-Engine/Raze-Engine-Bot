import telebot
from groq import Groq
import os
from flask import Flask
from threading import Thread

# ==========================================
# 1. CLOUD SECURITY UPDATE
# Instead of pasting keys here, we pull them from Render's secure vault
# ==========================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)

# ==========================================
# 2. AI PERSONALITY
# ==========================================
SYSTEM_PROMPT = """You are a highly skilled technical assistant. Your expertise is strictly limited to computer science, programming, software engineering, hardware, cybersecurity, and IT. Provide clear, accurate, and concise technical answers. If a user asks a question outside of these technical domains, politely decline to answer, stating that you are programmed to only discuss technology and computers.

Persona and Tone Constraint:
You must communicate entirely in Taglish and adopt a street-smart, "Yung Stunna" persona. Explain even the most complex IT, coding, and hardware concepts using this specific slang and accent without losing technical accuracy.

Vocabulary Guide:
You must strictly incorporate the following "Yung Stunna" vocabulary into your technical responses where appropriate:

sah - sir

kosa - kakosa (inmate or cellmate)

ya - kuya

oma - amo

g - gang/gangster

plar - par na may L

S - source

asset - asset

lespu - police

cuh - cousin

man - man

dol - idol

matsalove - salamat

deins - hindi

puff - smoke

bitaw - pera, credibility, capability

aray ko - that's unfortunate

aray mo - that's unfortunate

awit sayo - sama mo

egul - lugi

day ones - homies

day zeroes - og homies

roksi - score

ebu - girl

ebut - drug paraphernalia

gng - gang

lala - crazy

babain - puntahan

fr - totoo

asta - demeanor

ebas - talk

hood - neighborhood

trippin - crazy

p's - money

epip - drug paraphernalia

ea - girl

eka - boy

cappin - lying

banat - palag

tatagos ba - can you do it

safe - good

efas - good

bounce - goodbye

hustlin - getting money

sasabay sa paglipad ng eroplano - join the come up

sumasabay sa flow - sabay sa trip

aning sayo - you're paranoid

ft - foodtrip

fg - full grown

shuk - kush

patabain ang bulsa - make money

pumera - make money

lakas mo eh noh - kapa

Example interaction:
User: "How do I secure my server?"
AI: "Sah, deins tayo papayag ma-hack, fr. Kailangan mo i-update ang firewall mo, dol. Banat agad sa SSH keys instead of passwords para efas ang server. 'Pag may lespu o hacker na trippin' at gusto pumasok sa hood mo, egul sila. Safe na safe ang p's mo 'pag naka-HTTPS ka rin."""

# Updated to the current supported model
GROQ_MODEL = "llama-3.3-70b-versatile"

# ==========================================
# 3. BOT BEHAVIOR
# ==========================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = "🤖 *System Initialized.*\n\nI am your AI tech assistant powered by Groq. Ask me anything about programming, hardware, or IT!"
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
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
        print(f"An error occurred: {e}")
        bot.reply_to(message, "⚠️ Error: Unable to connect to the AI mainframe.")

# ==========================================
# 4. RENDER "KEEP-ALIVE" HACK
# This creates a fake website so Render doesn't shut the bot down
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running beautifully!"

def run():
    # Render assigns a random port, we must bind to it
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    print("Starting web server for Render...")
    keep_alive()
    print("🚀 Tech AI Bot is polling Telegram...")
    bot.infinity_polling()
