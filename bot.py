"""
bot.py
------
Bot Discord che invia un'immagine di benvenuto personalizzata quando
un nuovo utente entra nel server.

INSTALLAZIONE:
    pip install discord.py Pillow aiohttp

AVVIO:
    python bot.py

Tutte le impostazioni (token, canale, testi, colori, immagine di sfondo)
si modificano qui sotto, nella sezione CONFIGURAZIONE.
"""

import io
import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import aiohttp

# ======================================================================
# CONFIGURAZIONE - modifica qui tutto quello che ti serve
# ======================================================================

TOKEN = "INSERISCI_QUI_IL_TUO_TOKEN"          # Token del bot Discord
WELCOME_CHANNEL_ID = 0                         # ID del canale dove inviare il benvenuto (numero)

BACKGROUND_IMAGE = "background.png"            # Immagine di sfondo della card
CANVAS_WIDTH = 1000
CANVAS_HEIGHT = 400

# Avatar utente
AVATAR_SIZE = 260
AVATAR_X = 40
AVATAR_Y = -60

# Testo titolo (es. "Benvenuto Mario!")
TITLE_TEXT = "Benvenuto {user}!"
TITLE_X = 175
TITLE_Y = 305
TITLE_SIZE = 42
TITLE_COLOR = (255, 255, 255)

# Testo sottotitolo (es. "Sei un nuovo membro")
SUBTITLE_TEXT = "Sei un nuovo membro!"
SUBTITLE_X = 175
SUBTITLE_Y = 355
SUBTITLE_SIZE = 26
SUBTITLE_COLOR = (255, 176, 59)

# Testo contatore membri (es. "Sei il membro #142")
MEMBER_COUNT_TEXT = "Sei il membro #{count}"
MEMBER_COUNT_X = 175
MEMBER_COUNT_Y = 265
MEMBER_COUNT_SIZE = 20
MEMBER_COUNT_COLOR = (220, 220, 220)

# Font (lascia None per usare il font di default di Pillow)
FONT_PATH = None
# Esempio se hai un font .ttf nella stessa cartella:
# FONT_PATH = "font.ttf"

# ======================================================================
# FINE CONFIGURAZIONE
# ======================================================================

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)


def get_font(size: int) -> ImageFont.FreeTypeFont:
    if FONT_PATH:
        try:
            return ImageFont.truetype(FONT_PATH, size)
        except (OSError, IOError):
            pass
    return ImageFont.load_default(size=size)


def make_circle_avatar(avatar_bytes: bytes, size: int) -> Image.Image:
    img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
    img = img.resize((size, size), Image.LANCZOS)

    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)

    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(img, (0, 0), mask)
    return output


def draw_text_with_shadow(draw, text, x, y, font, color):
    draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=color)


async def fetch_bytes(url: str) -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.read()


async def generate_welcome_image(member: discord.Member) -> io.BytesIO:
    base = Image.open(BACKGROUND_IMAGE).convert("RGBA")
    base = base.resize((CANVAS_WIDTH, CANVAS_HEIGHT), Image.LANCZOS)

    overlay = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rectangle(
        (0, CANVAS_HEIGHT - 130, CANVAS_WIDTH, CANVAS_HEIGHT), fill=(0, 0, 0, 140)
    )
    base = Image.alpha_composite(base, overlay)

    draw = ImageDraw.Draw(base)

    avatar_bytes = await fetch_bytes(member.display_avatar.replace(size=256).url)
    avatar = make_circle_avatar(avatar_bytes, AVATAR_SIZE)
    base.paste(avatar, (AVATAR_X, AVATAR_Y), avatar)

    title = TITLE_TEXT.replace("{user}", member.display_name)
    subtitle = SUBTITLE_TEXT
    member_count = MEMBER_COUNT_TEXT.replace("{count}", str(member.guild.member_count))

    draw_text_with_shadow(draw, member_count, MEMBER_COUNT_X, MEMBER_COUNT_Y,
                           get_font(MEMBER_COUNT_SIZE), MEMBER_COUNT_COLOR)
    draw_text_with_shadow(draw, title, TITLE_X, TITLE_Y,
                           get_font(TITLE_SIZE), TITLE_COLOR)
    draw_text_with_shadow(draw, subtitle, SUBTITLE_X, SUBTITLE_Y,
                           get_font(SUBTITLE_SIZE), SUBTITLE_COLOR)

    buffer = io.BytesIO()
    base.convert("RGB").save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


@bot.event
async def on_ready():
    print(f"Bot connesso come {bot.user}")


@bot.event
async def on_member_join(member: discord.Member):
    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if channel is None:
        print("⚠️ Canale di benvenuto non trovato, controlla WELCOME_CHANNEL_ID")
        return

    image_buffer = await generate_welcome_image(member)
    file = discord.File(image_buffer, filename="welcome.png")
    await channel.send(file=file)


if __name__ == "__main__":
    bot.run(TOKEN)
