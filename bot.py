"""
███╗   ██╗ ██████╗ ██╗   ██╗ █████╗ ██╗
████╗  ██║██╔═══██╗██║   ██║██╔══██╗██║
██╔██╗ ██║██║   ██║██║   ██║███████║██║
██║╚██╗██║██║   ██║╚██╗ ██╔╝██╔══██║██║
██║ ╚████║╚██████╔╝ ╚████╔╝ ██║  ██║██║
╚═╝  ╚═══╝ ╚═════╝   ╚═══╝  ╚═╝  ╚═╝╚═╝

NovAI — Discord bot powered by Pollinations AI
Text · Images · Audio · Video · BYOP
"""

import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import os
import json
import io
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
#  CONFIG
# ──────────────────────────────────────────────
DISCORD_TOKEN    = os.getenv("DISCORD_TOKEN", "")
BASE_URL         = "https://gen.pollinations.ai/v1"
BOT_NAME         = "NovAI"
BOT_COLOR        = 0x5865F2   # blurple Discord
BOT_VERSION      = "1.0.0"

# Chiavi per utente { user_id: "sk_..." }
USER_KEYS: dict[int, str] = {}

# Modelli per utente { user_id: { tipo: modello } }
USER_MODELS: dict[int, dict] = {}

# Thread di chat attivi { thread_id: { user_id, model, history: [...] } }
CHAT_THREADS: dict[int, dict] = {}

DEFAULT_MODELS = {
    "text":  "openai",
    "image": "flux",
    "audio": "nova",
    "video": "seedance",
}

KNOWN_MODELS = {
    "text":  ["openai", "claude", "gemini", "deepseek", "mistral", "qwen", "mercury", "llama"],
    "image": ["flux", "gptimage-large", "seedream", "kontext", "flux-realism"],
    "audio": ["nova", "alloy", "echo", "fable", "onyx", "shimmer"],
    "video": ["seedance", "wan", "hunyuan"],
}

TYPE_EMOJI = {"text": "💬", "image": "🖼️", "audio": "🔊", "video": "🎬"}

# ──────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────

def get_key(user_id: int) -> str | None:
    return USER_KEYS.get(user_id) or os.getenv("POLLINATIONS_KEY") or None

def get_model(user_id: int, tipo: str) -> str:
    return USER_MODELS.get(user_id, {}).get(tipo, DEFAULT_MODELS[tipo])

def auth_headers(key: str) -> dict:
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type":  "application/json",
    }

async def api_post_json(session: aiohttp.ClientSession, url: str, payload: dict, key: str) -> dict:
    async with session.post(url, headers=auth_headers(key), json=payload) as resp:
        resp.raise_for_status()
        return await resp.json()

async def api_post_bytes(session: aiohttp.ClientSession, url: str, payload: dict, key: str) -> bytes:
    async with session.post(url, headers=auth_headers(key), json=payload) as resp:
        resp.raise_for_status()
        return await resp.read()

async def api_get_bytes(session: aiohttp.ClientSession, url: str) -> bytes:
    async with session.get(url) as resp:
        resp.raise_for_status()
        return await resp.read()

def no_key_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🔑 No API key connected",
        description=(
            "You need to connect your Pollinations key first!\n\n"
            "**→ Use `/connect` and paste your `sk_...` key**\n\n"
            "Get your key at [enter.pollinations.ai](https://enter.pollinations.ai)"
        ),
        color=0xED4245
    )
    return embed

# ──────────────────────────────────────────────
#  BOT SETUP
# ──────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="pollinations.ai ✨"
        )
    )
    print(f"✅  {BOT_NAME} v{BOT_VERSION} online as {bot.user}")

# ──────────────────────────────────────────────
#  /connect — BYOP
# ──────────────────────────────────────────────
@bot.tree.command(name="connect", description="Connect your Pollinations API key (BYOP)")
@app_commands.describe(key="Your Pollinations secret key (sk_...)")
async def cmd_connect(interaction: discord.Interaction, key: str):
    # Rispondi in modo privato così la chiave non è visibile agli altri
    if not key.startswith("sk_") and not key.startswith("pk_"):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Invalid key format",
                description="The key must start with `sk_` (secret) or `pk_` (publishable).\nGet yours at [enter.pollinations.ai](https://enter.pollinations.ai)",
                color=0xED4245
            ),
            ephemeral=True
        )
        return

    # Testa la chiave facendo una chiamata leggera
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BASE_URL}/models",
                headers=auth_headers(key)
            ) as resp:
                if resp.status == 401:
                    raise Exception("Unauthorized")
                resp.raise_for_status()
    except Exception:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Key rejected",
                description="Pollinations didn't accept this key. Check it and try again.",
                color=0xED4245
            ),
            ephemeral=True
        )
        return

    USER_KEYS[interaction.user.id] = key
    masked = key[:6] + "•" * (len(key) - 9) + key[-3:]

    embed = discord.Embed(
        title="✅ Key connected!",
        description=f"Your Pollinations key has been saved.\n`{masked}`\n\nYou can now use all NovAI commands!",
        color=0x57F287
    )
    embed.set_footer(text="Only you can see this message • Key stored in memory only")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="disconnect", description="Remove your connected Pollinations key")
async def cmd_disconnect(interaction: discord.Interaction):
    if interaction.user.id in USER_KEYS:
        del USER_KEYS[interaction.user.id]
        msg = "✅ Your API key has been removed."
        color = 0x57F287
    else:
        msg = "You didn't have a key connected."
        color = 0xFEE75C

    await interaction.response.send_message(
        embed=discord.Embed(title=msg, color=color),
        ephemeral=True
    )

# ──────────────────────────────────────────────
#  /text — apre un thread di chat
# ──────────────────────────────────────────────
@bot.tree.command(name="text", description="Open an AI chat thread")
@app_commands.describe(
    prompt="Your first message",
    system="Optional system prompt (changes AI behavior)"
)
async def cmd_text(interaction: discord.Interaction, prompt: str, system: str = "You are a helpful assistant."):
    key = get_key(interaction.user.id)
    if not key:
        await interaction.response.send_message(embed=no_key_embed(), ephemeral=True)
        return

    model = get_model(interaction.user.id, "text")
    await interaction.response.defer(thinking=True)

    try:
        # Prima risposta AI
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user",   "content": prompt}
                ],
                "max_tokens": 1500,
            }
            data  = await api_post_json(session, f"{BASE_URL}/chat/completions", payload, key)
            reply = data["choices"][0]["message"]["content"]

        # Messaggio iniziale nel canale
        embed_intro = discord.Embed(
            description=f"**{interaction.user.display_name}:** {prompt}",
            color=BOT_COLOR
        )
        embed_intro.set_author(name=f"💬 NovAI Chat • {model}")
        embed_intro.set_footer(text="A thread has been opened — just type there to keep chatting!")
        msg = await interaction.followup.send(embed=embed_intro)

        # Crea il thread
        thread = await msg.create_thread(
            name=f"💬 {interaction.user.display_name} — {prompt[:40]}",
            auto_archive_duration=60
        )

        # Salva lo stato del thread
        CHAT_THREADS[thread.id] = {
            "user_id": interaction.user.id,
            "model":   model,
            "system":  system,
            "key":     key,
            "history": [
                {"role": "system",    "content": system},
                {"role": "user",      "content": prompt},
                {"role": "assistant", "content": reply},
            ]
        }

        # Manda la risposta nel thread
        embed_reply = discord.Embed(description=reply[:4000], color=BOT_COLOR)
        embed_reply.set_footer(text="Just type here to keep chatting • /close to end the chat")
        await thread.send(embed=embed_reply)

    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245))


# ──────────────────────────────────────────────
#  on_message — risponde nei thread di chat
# ──────────────────────────────────────────────
@bot.event
async def on_message(message: discord.Message):
    # Ignora messaggi del bot stesso
    if message.author.bot:
        return

    # Controlla se il messaggio è in un thread NovAI attivo
    if not isinstance(message.channel, discord.Thread):
        await bot.process_commands(message)
        return

    thread_data = CHAT_THREADS.get(message.channel.id)
    if not thread_data:
        await bot.process_commands(message)
        return

    # Processa solo messaggi dello stesso utente che ha aperto il thread
    if message.author.id != thread_data["user_id"]:
        return

    # Comando speciale /close dentro il thread
    if message.content.strip().lower() in ["/close", "!close"]:
        del CHAT_THREADS[message.channel.id]
        await message.channel.send(
            embed=discord.Embed(
                title="✅ Chat closed",
                description="This thread has been closed. Use `/text` to start a new chat!",
                color=0x57F287
            )
        )
        await message.channel.edit(archived=True, locked=True)
        return

    # Mostra "typing..."
    async with message.channel.typing():
        key     = thread_data["key"]
        model   = thread_data["model"]
        history = thread_data["history"]

        # Aggiungi messaggio utente alla history
        history.append({"role": "user", "content": message.content})

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model":    model,
                    "messages": history,
                    "max_tokens": 1500,
                }
                data  = await api_post_json(session, f"{BASE_URL}/chat/completions", payload, key)
                reply = data["choices"][0]["message"]["content"]

            # Aggiungi risposta alla history
            history.append({"role": "assistant", "content": reply})

            embed = discord.Embed(description=reply[:4000], color=BOT_COLOR)
            embed.set_footer(text=f"{model} • type /close to end")
            await message.channel.send(embed=embed)

        except Exception as e:
            await message.channel.send(
                embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245)
            )

# ──────────────────────────────────────────────
#  /image
# ──────────────────────────────────────────────
@bot.tree.command(name="image", description="Generate an image with AI")
@app_commands.describe(
    prompt="Describe the image you want",
    size="Image size (default: 1024x1024)"
)
@app_commands.choices(size=[
    app_commands.Choice(name="1024×1024 (square)",    value="1024x1024"),
    app_commands.Choice(name="1792×1024 (landscape)", value="1792x1024"),
    app_commands.Choice(name="1024×1792 (portrait)",  value="1024x1792"),
])
async def cmd_image(interaction: discord.Interaction, prompt: str, size: str = "1024x1024"):
    key = get_key(interaction.user.id)
    if not key:
        await interaction.response.send_message(embed=no_key_embed(), ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    model = get_model(interaction.user.id, "image")

    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model":  model,
                "prompt": prompt,
                "size":   size,
                "n":      1,
                "response_format": "url",
            }
            data = await api_post_json(session, f"{BASE_URL}/images/generations", payload, key)
            img_url   = data["data"][0]["url"]
            img_bytes = await api_get_bytes(session, img_url)

        file  = discord.File(fp=io.BytesIO(img_bytes), filename="novai.png")
        embed = discord.Embed(color=BOT_COLOR)
        embed.set_author(name=f"🖼️ {model} • {size}")
        embed.set_image(url="attachment://novai.png")
        embed.set_footer(text=prompt[:100])
        await interaction.followup.send(embed=embed, file=file)

    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245))

# ──────────────────────────────────────────────
#  /audio
# ──────────────────────────────────────────────
@bot.tree.command(name="audio", description="Convert text to speech")
@app_commands.describe(text="The text to convert to audio")
async def cmd_audio(interaction: discord.Interaction, text: str):
    key = get_key(interaction.user.id)
    if not key:
        await interaction.response.send_message(embed=no_key_embed(), ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    voice = get_model(interaction.user.id, "audio")

    try:
        async with aiohttp.ClientSession() as session:
            payload = {"model": "tts-1", "input": text, "voice": voice}
            audio   = await api_post_bytes(session, f"{BASE_URL}/audio/speech", payload, key)

        file = discord.File(fp=io.BytesIO(audio), filename="novai_audio.mp3")
        await interaction.followup.send(
            content=f"🔊 **Voice:** `{voice}` — *{text[:80]}{'...' if len(text)>80 else ''}*",
            file=file
        )

    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245))

# ──────────────────────────────────────────────
#  /video
# ──────────────────────────────────────────────
@bot.tree.command(name="video", description="Generate a video with AI")
@app_commands.describe(prompt="Describe the video you want to generate")
async def cmd_video(interaction: discord.Interaction, prompt: str):
    key = get_key(interaction.user.id)
    if not key:
        await interaction.response.send_message(embed=no_key_embed(), ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    model = get_model(interaction.user.id, "video")

    try:
        async with aiohttp.ClientSession() as session:
            payload = {"model": model, "prompt": prompt}
            data    = await api_post_json(session, f"{BASE_URL}/video/generations", payload, key)
            vid_url = data.get("data", [{}])[0].get("url", "")

            if not vid_url:
                raise Exception("No video URL returned by API")

            vid_bytes = await api_get_bytes(session, vid_url)

        file = discord.File(fp=io.BytesIO(vid_bytes), filename="novai_video.mp4")
        embed = discord.Embed(color=BOT_COLOR)
        embed.set_author(name=f"🎬 {model}")
        embed.set_footer(text=prompt[:100])
        await interaction.followup.send(embed=embed, file=file)

    except Exception as e:
        await interaction.followup.send(
            embed=discord.Embed(
                title="❌ Video error",
                description=f"`{e}`\n\n💡 Video generation may require Pollen credits at [enter.pollinations.ai](https://enter.pollinations.ai)",
                color=0xED4245
            )
        )

# ──────────────────────────────────────────────
#  /model — cambia modello
# ──────────────────────────────────────────────
@bot.tree.command(name="model", description="Change the AI model for text/image/audio/video")
@app_commands.describe(
    type="Generation type",
    name="Model name to use"
)
@app_commands.choices(type=[
    app_commands.Choice(name="💬 Text",  value="text"),
    app_commands.Choice(name="🖼️ Image", value="image"),
    app_commands.Choice(name="🔊 Audio", value="audio"),
    app_commands.Choice(name="🎬 Video", value="video"),
])
async def cmd_model(interaction: discord.Interaction, type: str, name: str):
    uid = interaction.user.id
    if uid not in USER_MODELS:
        USER_MODELS[uid] = dict(DEFAULT_MODELS)

    old = USER_MODELS[uid].get(type, DEFAULT_MODELS[type])
    USER_MODELS[uid][type] = name

    suggestions = " · ".join(f"`{m}`" for m in KNOWN_MODELS.get(type, []))
    embed = discord.Embed(title="✅ Model updated", color=0x57F287)
    embed.add_field(name="Type",    value=f"{TYPE_EMOJI[type]} {type}",  inline=True)
    embed.add_field(name="Before",  value=f"`{old}`",                    inline=True)
    embed.add_field(name="Now",     value=f"`{name}`",                   inline=True)
    embed.add_field(name="Suggestions", value=suggestions or "—",        inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ──────────────────────────────────────────────
#  /models — lista modelli
# ──────────────────────────────────────────────
@bot.tree.command(name="models", description="List available Pollinations models")
@app_commands.describe(type="Filter by type (optional)")
@app_commands.choices(type=[
    app_commands.Choice(name="All",    value="all"),
    app_commands.Choice(name="💬 Text",  value="text"),
    app_commands.Choice(name="🖼️ Image", value="image"),
    app_commands.Choice(name="🔊 Audio", value="audio"),
    app_commands.Choice(name="🎬 Video", value="video"),
])
async def cmd_models(interaction: discord.Interaction, type: str = "all"):
    await interaction.response.defer(thinking=True)
    key = get_key(interaction.user.id)

    embed = discord.Embed(title=f"📋 {BOT_NAME} — Available Models", color=BOT_COLOR)

    if key:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{BASE_URL}/models", headers=auth_headers(key)) as resp:
                    if resp.status == 200:
                        data   = await resp.json()
                        live   = [m["id"] for m in data.get("data", [])]
                        chunk  = "\n".join(f"`{m}`" for m in live[:50])
                        embed.add_field(name="Live from API", value=chunk or "—", inline=False)
                        embed.set_footer(text="Live list from Pollinations API")
                        await interaction.followup.send(embed=embed)
                        return
        except Exception:
            pass

    # Fallback lista locale
    tipi = [type] if type != "all" else ["text", "image", "audio", "video"]
    for t in tipi:
        lista = "\n".join(f"`{m}`" for m in KNOWN_MODELS[t])
        embed.add_field(name=f"{TYPE_EMOJI[t]} {t.capitalize()}", value=lista, inline=True)
    embed.set_footer(text="Connect your key with /connect to see the full live list")
    await interaction.followup.send(embed=embed)

# ──────────────────────────────────────────────
#  /info
# ──────────────────────────────────────────────
@bot.tree.command(name="info", description="Show your current NovAI settings")
async def cmd_info(interaction: discord.Interaction):
    uid    = interaction.user.id
    key    = get_key(uid)
    models = USER_MODELS.get(uid, DEFAULT_MODELS)

    embed = discord.Embed(title=f"⚙️ {BOT_NAME} — Your Settings", color=BOT_COLOR)

    # Stato connessione
    if USER_KEYS.get(uid):
        k = USER_KEYS[uid]
        masked = k[:6] + "•" * (len(k) - 9) + k[-3:]
        embed.add_field(name="🔑 Key", value=f"`{masked}` ✅", inline=False)
    elif os.getenv("POLLINATIONS_KEY"):
        embed.add_field(name="🔑 Key", value="Using server default key", inline=False)
    else:
        embed.add_field(name="🔑 Key", value="❌ Not connected — use `/connect`", inline=False)

    # Modelli
    for tipo in ["text", "image", "audio", "video"]:
        m = models.get(tipo, DEFAULT_MODELS[tipo])
        embed.add_field(name=f"{TYPE_EMOJI[tipo]} {tipo.capitalize()}", value=f"`{m}`", inline=True)

    embed.set_footer(text=f"{BOT_NAME} v{BOT_VERSION} • Powered by Pollinations AI")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ──────────────────────────────────────────────
#  /help
# ──────────────────────────────────────────────
@bot.tree.command(name="help", description="Show all NovAI commands")
async def cmd_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title=f"✨ {BOT_NAME} — Commands",
        description="AI-powered bot by Pollinations",
        color=BOT_COLOR
    )
    embed.add_field(name="🔑 Setup",      value="`/connect` — Connect your Pollinations key (BYOP)\n`/disconnect` — Remove your key\n`/info` — View your settings", inline=False)
    embed.add_field(name="💬 Generate",   value="`/text` — Generate text\n`/image` — Generate an image\n`/audio` — Text to speech\n`/video` — Generate a video", inline=False)
    embed.add_field(name="⚙️ Models",     value="`/model` — Change AI model\n`/models` — List available models", inline=False)
    embed.set_footer(text=f"{BOT_NAME} v{BOT_VERSION} • enter.pollinations.ai")
    await interaction.response.send_message(embed=embed)

# ──────────────────────────────────────────────
#  START
# ──────────────────────────────────────────────
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌  DISCORD_TOKEN missing in .env!")
        exit(1)
    print(f"🚀  Starting {BOT_NAME} v{BOT_VERSION}...")
    bot.run(DISCORD_TOKEN)
