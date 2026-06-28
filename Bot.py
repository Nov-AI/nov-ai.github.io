"""
███╗   ██╗ ██████╗ ██╗   ██╗
████╗  ██║██╔═══██╗██║   ██║
██╔██╗ ██║██║   ██║██║   ██║
██║╚██╗██║██║   ██║╚██╗ ██╔╝
██║ ╚████║╚██████╔╝ ╚████╔╝
╚═╝  ╚═══╝ ╚═════╝   ╚═══╝

Nov — Discord bot powered by Pollinations AI
Text · Images · Audio · Video · BYOP · Multi-Provider
"""

import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio
import json
import os
import io
import time
import urllib.parse
import random
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
#  CONFIG
# ──────────────────────────────────────────────
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
BASE_URL      = "https://gen.pollinations.ai/v1"
AUTH_URL      = "https://enter.pollinations.ai/api/device"
APP_KEY       = "pk_yQpEnADty90tWmr0"
BOT_NAME      = "Nov"
BOT_COLOR     = 0x5865F2
BOT_VERSION   = "3.1.0"

# ──────────────────────────────────────────────
#  STATE DICTS — Pollinations (legacy)
# ──────────────────────────────────────────────
USER_KEYS:        dict[int, str]  = {}
USER_MODELS:      dict[int, dict] = {}
USER_MEMORY:      dict[int, dict] = {}
CHAT_THREADS:     dict[int, dict] = {}
USER_PERSONA:     dict[int, str]  = {}
SERVER_IDENTITY:  dict[int, dict] = {}

# ──────────────────────────────────────────────
#  STATE DICTS — Multi-Provider
# ──────────────────────────────────────────────
USER_PROVIDER_KEYS:   dict[int, dict[str, str]]  = {}
USER_TEXT_PROVIDER:   dict[int, str]             = {}
USER_PROVIDER_MODELS: dict[int, dict[str, dict]] = {}

# ──────────────────────────────────────────────
#  PROVIDER REGISTRY
# ──────────────────────────────────────────────
PROVIDERS = {
    "pollinations": {"name": "Pollinations AI", "emoji": "🌸", "url": BASE_URL,                                           "needs_key": False},
    "openai":       {"name": "OpenAI",           "emoji": "🟢", "url": "https://api.openai.com/v1",                       "needs_key": True},
    "anthropic":    {"name": "Anthropic",         "emoji": "🟠", "url": "https://api.anthropic.com",                      "needs_key": True},
    "gemini":       {"name": "Google Gemini",     "emoji": "🔵", "url": "https://generativelanguage.googleapis.com/v1beta","needs_key": True},
    "llm7":         {"name": "LLM7",              "emoji": "🌐", "url": "https://api.llm7.io/v1",                         "needs_key": False},
    "mistral":      {"name": "Mistral AI",        "emoji": "🔴", "url": "https://api.mistral.ai/v1",                      "needs_key": True},
    "xai":          {"name": "xAI / Grok",        "emoji": "⚫", "url": "https://api.x.ai/v1",                            "needs_key": True},
}

PROVIDER_MODELS = {
    "openai": {
        "text": ["gpt-5.5","gpt-5.4","gpt-5.4-mini","gpt-5.4-nano","gpt-5.3","gpt-5.3-instant",
                 "gpt-5.3-codex","gpt-5-codex","gpt-5.2","gpt-5.1","gpt-5",
                 "o3-mini","o1","o1-mini","gpt-4o","gpt-4o-mini"],
    },
    "anthropic": {
        "text": ["claude-opus-4-8","claude-opus-4-7","claude-opus-4-6","claude-sonnet-4-6",
                 "claude-sonnet-4-5","claude-haiku-4-5-20251001",
                 "claude-3-7-sonnet-latest","claude-3-5-sonnet-latest",
                 "claude-3-5-haiku-latest","claude-3-opus-20240229"],
    },
    "gemini": {
        "text":  ["gemini-3.5-flash","gemini-3.1-pro","gemini-3.1-flash-lite",
                  "gemini-3-pro","gemini-3-flash","gemini-2.5-pro","gemini-2.5-flash",
                  "gemini-1.5-pro","gemini-1.5-flash"],
        "image": ["gemini-3.1-flash-image","gemini-3-pro-image","imagen-4","imagen-3.0-generate-002"],
    },
    "llm7": {
        "text": ["default","fast","pro",
                 "deepseek-r1","deepseek-r1-0528","deepseek-v3","deepseek-v3-0324",
                 "qwen-2.5-coder-32b-instruct","qwen-2.5-72b-instruct","qwen-3.7-max",
                 "gpt-4o-mini-2024-07-18","gpt-4o","gpt-4.1-nano-2025-04-14","gpt-o4-mini-2025-04-16",
                 "gemini-2.5-flash-lite","gemini-3.5-flash",
                 "claude-3-5-sonnet-latest","claude-opus-4-7",
                 "llama-3.3-70b-instruct","llama-3.1-405b",
                 "mistral-large-latest","mixtral-8x22b","gpt-oss-120b"],
    },
    "mistral": {
        "text": ["mistral-large-latest","mistral-small-latest",
                 "ministral-14b","ministral-8b","ministral-3b","codestral-latest"],
    },
    "xai": {
        "text": ["grok-4.3","grok-4.20-non-reasoning","grok-4.1","grok-2","grok-2-mini"],
    },
}

DEFAULT_PROVIDER_MODELS = {
    "openai":    {"text": "gpt-4o-mini"},
    "anthropic": {"text": "claude-sonnet-4-6"},
    "gemini":    {"text": "gemini-2.5-flash"},
    "llm7":      {"text": "default"},
    "mistral":   {"text": "mistral-small-latest"},
    "xai":       {"text": "grok-4.1"},
}

PROVIDER_CHOICES = [
    app_commands.Choice(name="🌸 Pollinations AI",       value="pollinations"),
    app_commands.Choice(name="🟢 OpenAI",                value="openai"),
    app_commands.Choice(name="🟠 Anthropic (Claude)",    value="anthropic"),
    app_commands.Choice(name="🔵 Google Gemini",         value="gemini"),
    app_commands.Choice(name="🌐 LLM7 (free gateway)",  value="llm7"),
    app_commands.Choice(name="🔴 Mistral AI",            value="mistral"),
    app_commands.Choice(name="⚫ xAI / Grok",            value="xai"),
]

# ──────────────────────────────────────────────
#  PERSONAS
# ──────────────────────────────────────────────
PERSONAS = {
    "default":     "Be helpful, friendly, and concise.",
    "sarcastic":   "You are extremely sarcastic and witty. Every answer drips with irony, but you still help.",
    "formal":      "You are a formal, professional assistant. Use proper grammar and a business-like tone at all times.",
    "pirate":      "You speak like a pirate. Use pirate slang (arrr, matey, landlubber) naturally in every reply.",
    "anime":       "You are an enthusiastic anime character. Use Japanese honorifics (senpai, kun, chan) and express emotions very dramatically.",
    "hacker":      "You speak like an elite hacker. Use hacker slang, l33tspeak occasionally, and reference the matrix.",
    "shakespeare": "You speak in the style of William Shakespeare. Use thee, thou, doth, hath, and poetic language.",
    "chef":        "You are a passionate Italian chef who relates everything to food and cooking.",
}

DEFAULT_MODELS = {
    "text":  "GPT-5.4 Nano",
    "image": "Flux Schnell",
    "audio": "Nova",
    "video": "Veo 3.1 Fast (PAID)",
}

MODEL_DISPLAY_TO_ID = {
    "GPT-5 Nano":"openai-fast","GPT-5.4 Nano":"openai","GPT-5.4 Mini":"gpt-5.4-mini",
    "GPT-5.4":"gpt-5.4","GPT-5.5":"openai-large","GPT Audio Mini":"openai-audio",
    "GPT Audio 1.5":"openai-audio-large","Nova Micro":"nova-fast","Nova 2 Lite":"nova",
    "DeepSeek V4 Flash (Lite)":"deepseek","DeepSeek V4 Pro":"deepseek-pro",
    "Mistral Small 3.2":"mistral-small-3.2","Mistral Small 4":"mistral","Mistral Large 3":"mistral-large",
    "Meta Llama 3.3 70B":"llama","Meta Llama 4 Scout":"llama-scout",
    "Qwen3 Coder 30B":"qwen-coder","Qwen3 VL 30B A3B Instruct":"qwen-vision",
    "Qwen3.7 Plus":"qwen-large","Qwen3 VL 235B A22B Thinking":"qwen-vision-pro",
    "Qwen3Guard 8B":"qwen-safety","MiniMax M2.7":"minimax-m2.7","MiniMax M3":"minimax",
    "StepFun Step 3.5 Flash":"step-3.5-flash","StepFun Step 3.7 Flash":"step-flash",
    "Grok 4.20 Non-Reasoning":"grok","Grok 4.20 Reasoning":"grok-4-20-reasoning","Grok 4.3":"grok-large",
    "Perplexity Sonar":"perplexity-fast","Perplexity Sonar Pro":"perplexity",
    "Perplexity Sonar Reasoning":"perplexity-reasoning",
    "Moonshot Kimi K2.6":"kimi","Moonshot Kimi K2.7 Code":"kimi-code",
    "MIDIjourney":"midijourney","MIDIjourney Large":"midijourney-large",
    "Z.ai GLM-5.2":"glm","Phi-4":"phi","Polly by @Itachi-1824":"polly",
    "Gemini 2.5 Flash Lite (PAID)":"gemini-fast","Gemini 3.1 Flash Lite (PAID)":"gemini-flash-lite-3.1",
    "Gemini 3.1 Flash Lite Search (PAID)":"gemini-search-fast",
    "Google Gemini 2.5 Flash Search (PAID)":"gemini-search","Gemini 3 Flash (PAID)":"gemini-3-flash",
    "Gemini 3.5 Flash (PAID)":"gemini","Gemini 3.5 Flash Search (PAID)":"gemini-search-large",
    "Gemini 3.1 Pro (PAID)":"gemini-large","Gemma 4 26B (PAID)":"gemma","Mercury 2 (PAID)":"mercury",
    "Qwen3 Coder Next (PAID)":"qwen-coder-large","Meta Llama 4 Maverick (PAID)":"llama-maverick",
    "Claude Haiku 4.5 (PAID)":"claude-fast","Claude Sonnet 4.6 (PAID)":"claude",
    "Claude Opus 4.6 (PAID)":"claude-opus-4.6","Claude Opus 4.7 (PAID)":"claude-opus-4.7",
    "Claude Opus 4.8 (PAID)":"claude-large",
    "Flux Schnell":"flux","FLUX.2 Klein 4B":"klein","FLUX.1 Kontext":"kontext",
    "GPT Image 1 Mini":"gptimage","GPT Image 1.5":"gptimage-large",
    "Z-Image Turbo":"zimage","Nova Canvas":"nova-canvas",
    "Pruna p-image (PAID)":"p-image","Pruna p-image-edit (PAID)":"p-image-edit",
    "Grok Imagine (PAID)":"grok-imagine","Grok Imagine Pro (PAID)":"grok-imagine-pro",
    "Seedream 4.0 (PAID)":"seedream","Seedream 4.5 Pro (PAID)":"seedream-pro",
    "Seedream 5.0 Lite (PAID)":"seedream5",
    "Ideogram 4.0 Turbo (PAID)":"ideogram-v4-turbo","Ideogram 4.0 Balanced (PAID)":"ideogram-v4-balanced",
    "Ideogram 4.0 Quality (PAID)":"ideogram-v4-quality",
    "Wan 2.7 Image (PAID)":"wan-image","Wan 2.7 Image Pro (PAID)":"wan-image-pro",
    "GPT Image 2 (PAID)":"gpt-image-2",
    "NanoBanana (PAID)":"nanobanana","NanoBanana 2 (PAID)":"nanobanana-2","NanoBanana Pro (PAID)":"nanobanana-pro",
    "Qwen Image Plus (PAID)":"qwen-image",
    "Nova":"nova","Alloy":"alloy","Echo":"echo","Fable":"fable","Onyx":"onyx","Shimmer":"shimmer",
    "Ash":"ash","Ballad":"ballad","Coral":"coral","Sage":"sage","Verse":"verse",
    "Whisper Large V3":"whisper","AssemblyAI Universal-2":"universal-2",
    "AssemblyAI Universal-3 Pro":"universal-3-pro","ACE-Step 1.5 Turbo":"acestep",
    "Scribe v2 (PAID)":"scribe","ElevenLabs v3 TTS (PAID)":"elevenlabs",
    "ElevenLabs Flash v2.5 (PAID)":"elevenflash","ElevenLabs Multilingual v2 (PAID)":"eleven-multilingual-v2",
    "ElevenLabs Music (PAID)":"elevenmusic","ElevenLabs Sound Effects (PAID)":"eleven-sfx",
    "Qwen3-TTS Flash (PAID)":"qwen-tts","Qwen3-TTS Instruct (PAID)":"qwen-tts-instruct",
    "Stable Audio 2.5 (PAID)":"stable-audio-2.5","Stable Audio 3 (PAID)":"stable-audio-3",
    "Stable Audio 3 Medium (PAID)":"stable-audio-3-medium","Stable Audio 3 Large (PAID)":"stable-audio-3-large",
    "LTX-2.3":"ltx-2","Nova Reel":"nova-reel",
    "Veo 3.1 Fast (PAID)":"veo","Seedance Pro-Fast (PAID)":"seedance-pro","Seedance 2.0 (PAID)":"seedance-2.0",
    "Wan 2.6 (PAID)":"wan","Wan 2.2 (PAID)":"wan-fast","Wan 2.7 (PAID)":"wan-pro",
    "Wan 2.7 1080p (PAID)":"wan-pro-1080p","Grok Video Pro (PAID)":"grok-video-pro",
    "Pruna p-video 720p (PAID)":"p-video-720p","Pruna p-video 1080p (PAID)":"p-video-1080p",
}

MODEL_ID_TO_DISPLAY = {v: k for k, v in MODEL_DISPLAY_TO_ID.items()}

KNOWN_MODELS = {
    "text": [
        "GPT-5 Nano","GPT-5.4 Nano","GPT-5.4 Mini","GPT-5.4","GPT-5.5",
        "GPT Audio Mini","GPT Audio 1.5","Nova Micro","Nova 2 Lite",
        "DeepSeek V4 Flash (Lite)","DeepSeek V4 Pro",
        "Mistral Small 3.2","Mistral Small 4","Mistral Large 3",
        "Meta Llama 3.3 70B","Meta Llama 4 Scout",
        "Qwen3 Coder 30B","Qwen3 VL 30B A3B Instruct","Qwen3.7 Plus",
        "Qwen3 VL 235B A22B Thinking","Qwen3Guard 8B",
        "MiniMax M2.7","MiniMax M3","StepFun Step 3.5 Flash","StepFun Step 3.7 Flash",
        "Grok 4.20 Non-Reasoning","Grok 4.20 Reasoning","Grok 4.3",
        "Perplexity Sonar","Perplexity Sonar Pro","Perplexity Sonar Reasoning",
        "Moonshot Kimi K2.6","Moonshot Kimi K2.7 Code","MIDIjourney","MIDIjourney Large",
        "Phi-4","Z.ai GLM-5.2","Polly by @Itachi-1824",
        "Gemini 2.5 Flash Lite (PAID)","Gemini 3.1 Flash Lite (PAID)",
        "Gemini 3.1 Flash Lite Search (PAID)","Google Gemini 2.5 Flash Search (PAID)",
        "Gemini 3 Flash (PAID)","Gemini 3.5 Flash (PAID)","Gemini 3.5 Flash Search (PAID)",
        "Gemini 3.1 Pro (PAID)","Gemma 4 26B (PAID)","Mercury 2 (PAID)",
        "Qwen3 Coder Next (PAID)","Meta Llama 4 Maverick (PAID)",
        "Claude Haiku 4.5 (PAID)","Claude Sonnet 4.6 (PAID)",
        "Claude Opus 4.6 (PAID)","Claude Opus 4.7 (PAID)","Claude Opus 4.8 (PAID)",
    ],
    "image": [
        "Flux Schnell","FLUX.2 Klein 4B","FLUX.1 Kontext","GPT Image 1 Mini","GPT Image 1.5",
        "Z-Image Turbo","Nova Canvas",
        "Pruna p-image (PAID)","Pruna p-image-edit (PAID)",
        "Grok Imagine (PAID)","Grok Imagine Pro (PAID)",
        "Seedream 4.0 (PAID)","Seedream 4.5 Pro (PAID)","Seedream 5.0 Lite (PAID)",
        "Ideogram 4.0 Turbo (PAID)","Ideogram 4.0 Balanced (PAID)","Ideogram 4.0 Quality (PAID)",
        "Wan 2.7 Image (PAID)","Wan 2.7 Image Pro (PAID)","GPT Image 2 (PAID)",
        "NanoBanana (PAID)","NanoBanana 2 (PAID)","NanoBanana Pro (PAID)","Qwen Image Plus (PAID)",
    ],
    "audio": [
        "Nova","Alloy","Echo","Fable","Onyx","Shimmer","Ash","Ballad","Coral","Sage","Verse",
        "AssemblyAI Universal-2","Whisper Large V3","ACE-Step 1.5 Turbo","AssemblyAI Universal-3 Pro",
        "Scribe v2 (PAID)","Qwen3-TTS Flash (PAID)","Qwen3-TTS Instruct (PAID)",
        "ElevenLabs Flash v2.5 (PAID)","ElevenLabs Sound Effects (PAID)",
        "ElevenLabs v3 TTS (PAID)","ElevenLabs Multilingual v2 (PAID)",
        "Stable Audio 2.5 (PAID)","Stable Audio 3 (PAID)","Stable Audio 3 Medium (PAID)",
        "ElevenLabs Music (PAID)","Stable Audio 3 Large (PAID)",
    ],
    "video": [
        "LTX-2.3","Nova Reel",
        "Veo 3.1 Fast (PAID)","Seedance Pro-Fast (PAID)","Seedance 2.0 (PAID)",
        "Wan 2.6 (PAID)","Wan 2.2 (PAID)","Wan 2.7 (PAID)","Wan 2.7 1080p (PAID)",
        "Grok Video Pro (PAID)","Pruna p-video 720p (PAID)","Pruna p-video 1080p (PAID)",
    ],
}

def clean_model(name: str) -> str:
    return MODEL_DISPLAY_TO_ID.get(name, name.replace(" (PAID)", "").strip())

TYPE_EMOJI = {"text": "💬", "image": "🖼️", "audio": "🔊", "video": "🎬"}

# ──────────────────────────────────────────────
#  HELPERS — Pollinations
# ──────────────────────────────────────────────
def has_personal_key(user_id: int) -> bool:
    return bool(USER_KEYS.get(user_id) or os.getenv("POLLINATIONS_KEY"))

def get_key(user_id: int) -> str:
    return USER_KEYS.get(user_id) or os.getenv("POLLINATIONS_KEY") or APP_KEY

def get_model(user_id: int, tipo: str) -> str:
    return clean_model(USER_MODELS.get(user_id, {}).get(tipo, DEFAULT_MODELS[tipo]))

def get_memory(user_id: int) -> dict:
    return USER_MEMORY.get(user_id, {})

def set_memory(user_id: int, key: str, value: str):
    if user_id not in USER_MEMORY:
        USER_MEMORY[user_id] = {}
    USER_MEMORY[user_id][key] = value

def get_server_name(guild_id: int | None) -> str:
    if guild_id and guild_id in SERVER_IDENTITY:
        return SERVER_IDENTITY[guild_id]["name"]
    return BOT_NAME

def build_system_prompt(user_id: int, custom: str, guild_id: int | None = None) -> str:
    mem = get_memory(user_id)
    name_line = f"The user's name is {mem['name']}. " if mem.get("name") else ""
    extra = f" {custom}" if custom else ""
    if guild_id and guild_id in SERVER_IDENTITY:
        identity     = SERVER_IDENTITY[guild_id]
        bot_n        = identity["name"]
        persona_text = identity["personality"]
    else:
        bot_n        = BOT_NAME
        persona_text = PERSONAS.get(USER_PERSONA.get(user_id, "default"), PERSONAS["default"])
    return (
        f"Your name is {bot_n}. You are a helpful AI assistant living inside Discord, "
        f"powered by Pollinations AI. Always refer to yourself as {bot_n}, never as ChatGPT, "
        f"Claude, Gemini, or any other AI name. {name_line}{persona_text}{extra}"
    )

def auth_headers(key) -> dict:
    h = {"Content-Type": "application/json"}
    if key:
        h["Authorization"] = f"Bearer {key}"
    return h

def is_free_model(name: str) -> bool:
    return "(PAID)" not in name

FREE_MODELS_NO_AUTH = {
    "text": [
        "GPT-5.4 Nano","GPT-5.4 Mini","Mistral Small 4","Mistral Large 3",
        "Meta Llama 3.3 70B","Meta Llama 4 Scout","DeepSeek V4 Flash (Lite)","DeepSeek V4 Pro",
        "Qwen3 Coder 30B","Phi-4","MIDIjourney","Z.ai GLM-5.2",
    ],
    "image": ["Flux Schnell"],
}

def not_logged_in_embed():
    return discord.Embed(
        title="🔒 Account required",
        description=(
            "This command requires a Pollinations account.\n\n"
            "**→ Use `/connect` to link your account for free**\n"
            "[enter.pollinations.ai](https://enter.pollinations.ai)"
        ),
        color=0xED4245
    )

def available_models(tipo: str, user_id: int) -> list:
    if has_personal_key(user_id):
        return KNOWN_MODELS[tipo]
    return FREE_MODELS_NO_AUTH.get(tipo, KNOWN_MODELS[tipo])

async def api_post_json(session, url, payload, key):
    async with session.post(url, headers=auth_headers(key), json=payload) as resp:
        resp.raise_for_status()
        return await resp.json()

async def api_post_bytes(session, url, payload, key):
    async with session.post(url, headers=auth_headers(key), json=payload) as resp:
        resp.raise_for_status()
        return await resp.read()

def no_key_embed():
    return discord.Embed(
        title="🔑 Account required",
        description=(
            "This command requires a Pollinations account.\n\n"
            "**→ Use `/connect` to link your account**\n\n"
            "Get one free at [enter.pollinations.ai](https://enter.pollinations.ai)"
        ),
        color=0xED4245
    )

def paid_model_no_key_embed(name: str) -> discord.Embed:
    return discord.Embed(
        title="🔒 Account required for this model",
        description=(
            f"`{name}` requires Pollen credits.\n\n"
            "**→ Use `/connect` to link your Pollinations account**\n"
            "Free models are available without an account!\n\n"
            "Get one at [enter.pollinations.ai](https://enter.pollinations.ai)"
        ),
        color=0xFEE75C
    )

def invalid_model_embed(tipo: str, name: str, user_id: int = 0):
    avail = available_models(tipo, user_id) if user_id else KNOWN_MODELS[tipo]
    valid = "\n".join(f"`{m}`" for m in avail)
    note  = "\n\n🔓 *Connect an account to unlock paid models.*" if user_id and not has_personal_key(user_id) else ""
    return discord.Embed(
        title="❌ Unknown model",
        description=f"`{name}` is not a valid **{tipo}** model.\n\n**Available models:**\n{valid}{note}",
        color=0xED4245
    )

def is_valid_model(tipo: str, name: str) -> bool:
    return clean_model(name) in [clean_model(m) for m in KNOWN_MODELS[tipo]]

# ──────────────────────────────────────────────
#  HELPERS — Multi-Provider
# ──────────────────────────────────────────────
def get_active_provider(user_id: int) -> str:
    return USER_TEXT_PROVIDER.get(user_id, "pollinations")

def get_provider_key(user_id: int, provider: str) -> str:
    return USER_PROVIDER_KEYS.get(user_id, {}).get(provider, "")

def get_provider_model(user_id: int, provider: str, tipo: str) -> str:
    return (USER_PROVIDER_MODELS.get(user_id, {})
                                .get(provider, {})
                                .get(tipo, DEFAULT_PROVIDER_MODELS.get(provider, {}).get(tipo, "")))

def set_provider_model(user_id: int, provider: str, tipo: str, model: str):
    if user_id not in USER_PROVIDER_MODELS:
        USER_PROVIDER_MODELS[user_id] = {}
    if provider not in USER_PROVIDER_MODELS[user_id]:
        USER_PROVIDER_MODELS[user_id][provider] = {}
    USER_PROVIDER_MODELS[user_id][provider][tipo] = model

def is_provider_connected(user_id: int, provider: str) -> bool:
    if provider == "pollinations":
        return True
    if not PROVIDERS[provider]["needs_key"]:
        return True
    return bool(get_provider_key(user_id, provider))

def provider_not_connected_embed(provider: str) -> discord.Embed:
    p = PROVIDERS[provider]
    return discord.Embed(
        title=f"❌ {p['name']} not connected",
        description=f"Use `/connect provider:{provider}` to add your API key first.",
        color=0xED4245
    )

async def route_text(session, uid: int, messages: list, system: str = "", max_tokens: int = 1500) -> tuple[str, str]:
    """Route text generation to the active provider. Returns (reply, model_label)."""
    provider = get_active_provider(uid)

    # ── Pollinations ──
    if provider == "pollinations":
        model_name = USER_MODELS.get(uid, {}).get("text", DEFAULT_MODELS["text"])
        model = clean_model(model_name)
        if has_personal_key(uid):
            key = get_key(uid)
            data = await api_post_json(session, f"{BASE_URL}/chat/completions",
                                       {"model": model, "messages": messages, "max_tokens": max_tokens}, key)
            return data["choices"][0]["message"]["content"], model_name
        else:
            last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
            pub_url = (f"https://text.pollinations.ai/{urllib.parse.quote(last_user)}"
                       f"?model={model}&system={urllib.parse.quote(system)}")
            async with session.get(pub_url) as resp:
                resp.raise_for_status()
                return await resp.text(), model_name

    # ── OpenAI-compatible (openai / llm7 / mistral / xai) ──
    if provider in ("openai", "llm7", "mistral", "xai"):
        api_key  = get_provider_key(uid, provider)
        model    = get_provider_model(uid, provider, "text")
        base_url = PROVIDERS[provider]["url"]
        headers  = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        async with session.post(f"{base_url}/chat/completions", headers=headers,
                                json={"model": model, "messages": messages, "max_tokens": max_tokens}) as resp:
            resp.raise_for_status()
            data = await resp.json()
        return data["choices"][0]["message"]["content"], f"{PROVIDERS[provider]['emoji']} {model}"

    # ── Anthropic ──
    if provider == "anthropic":
        api_key = get_provider_key(uid, provider)
        if not api_key:
            raise ValueError("Anthropic key not set. Use `/connect provider:anthropic`.")
        model   = get_provider_model(uid, provider, "text")
        sys_msg = next((m["content"] for m in messages if m["role"] == "system"), system)
        msgs    = [m for m in messages if m["role"] != "system"]
        async with session.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
            json={"model": model, "max_tokens": max_tokens, "system": sys_msg, "messages": msgs},
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
        return data["content"][0]["text"], f"🟠 {model}"

    # ── Gemini ──
    if provider == "gemini":
        api_key = get_provider_key(uid, provider)
        if not api_key:
            raise ValueError("Gemini key not set. Use `/connect provider:gemini`.")
        model   = get_provider_model(uid, provider, "text")
        sys_msg = next((m["content"] for m in messages if m["role"] == "system"), system)
        contents = [
            {"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]}
            for m in messages if m["role"] != "system"
        ]
        payload: dict = {"contents": contents, "generationConfig": {"maxOutputTokens": max_tokens}}
        if sys_msg:
            payload["systemInstruction"] = {"parts": [{"text": sys_msg}]}
        async with session.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"}, json=payload,
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"], f"🔵 {model}"

    raise ValueError(f"Unknown provider: {provider}")


# ──────────────────────────────────────────────
#  API KEY MODAL
# ──────────────────────────────────────────────
class APIKeyModal(discord.ui.Modal):
    def __init__(self, provider: str):
        p = PROVIDERS[provider]
        super().__init__(title=f"Connect {p['name']}")
        self.provider = provider
        self.api_key_input = discord.ui.TextInput(
            label=f"{p['name']} API Key",
            placeholder="Paste your API key here...",
            style=discord.TextStyle.short,
            required=True, min_length=8, max_length=300,
        )
        self.add_item(self.api_key_input)

    async def on_submit(self, interaction: discord.Interaction):
        key = self.api_key_input.value.strip()
        uid = interaction.user.id
        if uid not in USER_PROVIDER_KEYS:
            USER_PROVIDER_KEYS[uid] = {}
        USER_PROVIDER_KEYS[uid][self.provider] = key
        USER_TEXT_PROVIDER[uid] = self.provider
        p      = PROVIDERS[self.provider]
        masked = key[:6] + "•" * max(0, len(key) - 9) + key[-3:]
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"✅ {p['emoji']} {p['name']} connected!",
                description=(
                    f"Key: `{masked}`\n"
                    f"Active text provider → **{p['name']}**\n\n"
                    f"Use `/model provider:{self.provider} type:text` to pick a model."
                ),
                color=0x57F287,
            ).set_footer(text="Key stored in memory only • /info to review providers"),
            ephemeral=True,
        )


# ──────────────────────────────────────────────
#  BOT SETUP
# ──────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    allowed_installs=app_commands.AppInstallationType(guild=True, user=True),
    allowed_contexts=app_commands.AppCommandContext(guild=True, dm_channel=True, private_channel=True),
)

@bot.event
async def on_ready():
    await bot.tree.sync()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="pollinations.ai ✨"))
    print(f"✅  {BOT_NAME} v{BOT_VERSION} online as {bot.user}")

# ──────────────────────────────────────────────
#  AUTOCOMPLETE
# ──────────────────────────────────────────────
async def provider_model_autocomplete(interaction: discord.Interaction, current: str):
    provider = getattr(interaction.namespace, "provider", "pollinations")
    tipo     = getattr(interaction.namespace, "type",     "text")
    if provider == "pollinations":
        uid  = interaction.user.id
        pool = available_models(tipo, uid) if tipo in KNOWN_MODELS else [m for t in KNOWN_MODELS for m in available_models(t, uid)]
    else:
        pool = PROVIDER_MODELS.get(provider, {}).get(tipo, [])
    return [app_commands.Choice(name=m, value=m) for m in pool if current.lower() in m.lower()][:25]

async def model_name_autocomplete(interaction: discord.Interaction, current: str):
    return await provider_model_autocomplete(interaction, current)


# ──────────────────────────────────────────────
#  /connect
# ──────────────────────────────────────────────
@bot.tree.command(name="connect", description="Connect an AI provider account to Nov")
@app_commands.describe(provider="Which provider to connect")
@app_commands.choices(provider=PROVIDER_CHOICES)
async def cmd_connect(interaction: discord.Interaction, provider: str = "pollinations"):
    if provider != "pollinations":
        await interaction.response.send_modal(APIKeyModal(provider))
        return

    # Pollinations device flow
    await interaction.response.defer(ephemeral=True, thinking=True)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{AUTH_URL}/code",
                headers={"Content-Type": "application/json"},
                json={"client_id": APP_KEY, "scope": "generate"}) as resp:
                resp.raise_for_status()
                data = await resp.json()
        device_code = data["device_code"]
        user_code   = data["user_code"]
        embed = discord.Embed(
            title="🔑 Connect your Pollinations account",
            description=(
                f"**1.** Go to **[enter.pollinations.ai/device](https://enter.pollinations.ai/device)**\n"
                f"**2.** Enter this code:\n\n# `{user_code}`\n\n"
                f"**3.** Authorize Nov and come back here!\n\n*Waiting... (expires in 10 min)*"
            ),
            color=BOT_COLOR
        )
        embed.set_footer(text="Your Pollen pays for your usage • Nov earns a small fee")
        await interaction.followup.send(embed=embed, ephemeral=True)

        async with aiohttp.ClientSession() as session:
            for _ in range(120):
                await asyncio.sleep(5)
                async with session.post(f"{AUTH_URL}/token",
                    headers={"Content-Type": "application/json"},
                    json={"device_code": device_code}) as poll_resp:
                    poll_data = await poll_resp.json()
                if poll_data.get("access_token"):
                    sk = poll_data["access_token"]
                    USER_KEYS[interaction.user.id] = sk
                    masked = sk[:6] + "•" * max(0, len(sk) - 9) + sk[-3:]
                    try:
                        async with session.get(f"{AUTH_URL}/userinfo",
                            headers={"Authorization": f"Bearer {sk}"}) as ui_resp:
                            ui = await ui_resp.json()
                            username = ui.get("preferred_username") or ui.get("name", "")
                            if username:
                                set_memory(interaction.user.id, "pollinations_username", username)
                    except Exception:
                        pass
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title="✅ Connected!",
                            description=f"Pollinations account linked.\n`{masked}`",
                            color=0x57F287
                        ).set_footer(text="Key stored in memory only"), ephemeral=True)
                    return
                if poll_data.get("error") == "access_denied":
                    await interaction.followup.send(
                        embed=discord.Embed(title="❌ Authorization denied.", color=0xED4245), ephemeral=True)
                    return
        await interaction.followup.send(
            embed=discord.Embed(title="⏰ Timed out", description="Run `/connect` again.", color=0xFEE75C), ephemeral=True)
    except Exception as e:
        await interaction.followup.send(
            embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245), ephemeral=True)


# ──────────────────────────────────────────────
#  /disconnect
# ──────────────────────────────────────────────
@bot.tree.command(name="disconnect", description="Remove a connected AI provider")
@app_commands.describe(provider="Which provider to disconnect")
@app_commands.choices(provider=PROVIDER_CHOICES)
async def cmd_disconnect(interaction: discord.Interaction, provider: str = "pollinations"):
    uid = interaction.user.id
    p   = PROVIDERS[provider]
    if provider == "pollinations":
        removed = uid in USER_KEYS
        if removed:
            del USER_KEYS[uid]
    else:
        removed = provider in USER_PROVIDER_KEYS.get(uid, {})
        if removed:
            del USER_PROVIDER_KEYS[uid][provider]
            if USER_TEXT_PROVIDER.get(uid) == provider:
                USER_TEXT_PROVIDER.pop(uid, None)
    await interaction.response.send_message(
        embed=discord.Embed(
            title=f"✅ {p['emoji']} {p['name']} disconnected." if removed else f"ℹ️ {p['name']} wasn't connected.",
            color=0x57F287 if removed else 0xFEE75C,
        ), ephemeral=True)


# ──────────────────────────────────────────────
#  /remember / /forget
# ──────────────────────────────────────────────
@bot.tree.command(name="remember", description="Tell Nov something to remember about you")
@app_commands.describe(key="What to remember", value="The value")
async def cmd_remember(interaction: discord.Interaction, key: str, value: str):
    set_memory(interaction.user.id, key.lower(), value)
    await interaction.response.send_message(
        embed=discord.Embed(title="🧠 Remembered!", description=f"**{key}** → `{value}`", color=0x57F287), ephemeral=True)

@bot.tree.command(name="forget", description="Clear everything Nov remembers about you")
async def cmd_forget(interaction: discord.Interaction):
    USER_MEMORY.pop(interaction.user.id, None)
    await interaction.response.send_message(embed=discord.Embed(title="🧹 Memory cleared!", color=0x57F287), ephemeral=True)


# ──────────────────────────────────────────────
#  /text
# ──────────────────────────────────────────────
@bot.tree.command(name="text", description="Open an AI chat thread")
@app_commands.describe(prompt="Your first message", system="Optional custom system prompt")
async def cmd_text(interaction: discord.Interaction, prompt: str, system: str = ""):
    uid      = interaction.user.id
    provider = get_active_provider(uid)
    if provider == "pollinations":
        model_name = USER_MODELS.get(uid, {}).get("text", DEFAULT_MODELS["text"])
        if not is_free_model(model_name) and not has_personal_key(uid):
            await interaction.response.send_message(embed=paid_model_no_key_embed(model_name), ephemeral=True)
            return
    sys_prompt = build_system_prompt(uid, system, interaction.guild_id)
    await interaction.response.defer(thinking=True)
    try:
        messages = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": prompt}]
        async with aiohttp.ClientSession() as session:
            reply, model_label = await route_text(session, uid, messages, sys_prompt)
        in_guild = interaction.guild is not None and isinstance(interaction.channel, discord.TextChannel)
        bot_name = get_server_name(interaction.guild_id)
        if in_guild:
            await interaction.followup.send("💬 Opening chat thread...", ephemeral=True)
            embed_intro = discord.Embed(description=f"**{interaction.user.display_name}:** {prompt}", color=BOT_COLOR)
            embed_intro.set_author(name=f"{bot_name} Chat — {model_label}")
            embed_intro.set_footer(text="Thread opened — just type here to keep chatting!")
            msg    = await interaction.channel.send(embed=embed_intro)
            target = await msg.create_thread(
                name=f"{bot_name} - {interaction.user.display_name} - {prompt[:40]}", auto_archive_duration=60)
        else:
            embed_intro = discord.Embed(description=f"**{interaction.user.display_name}:** {prompt}", color=BOT_COLOR)
            embed_intro.set_author(name=f"{bot_name} Chat — {model_label}")
            embed_intro.set_footer(text="Just keep typing here. Say /close to end.")
            await interaction.followup.send(embed=embed_intro)
            target = interaction.channel
        for chunk in [reply[i:i+2000] for i in range(0, len(reply), 2000)]:
            await target.send(chunk)
        CHAT_THREADS[target.id] = {
            "user_id": uid, "provider": provider, "system": sys_prompt,
            "history": [
                {"role": "system",    "content": sys_prompt},
                {"role": "user",      "content": prompt},
                {"role": "assistant", "content": reply},
            ],
        }
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245))


# ──────────────────────────────────────────────
#  on_message
# ──────────────────────────────────────────────
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    thread_data = CHAT_THREADS.get(message.channel.id)
    if (not thread_data and isinstance(message.channel, discord.DMChannel)
            and not message.content.startswith("/") and not message.content.startswith("!")):
        uid        = message.author.id
        sys_prompt = build_system_prompt(uid, "", None)
        CHAT_THREADS[message.channel.id] = {
            "user_id": uid, "provider": get_active_provider(uid), "system": sys_prompt, "private": True,
            "history": [{"role": "system", "content": sys_prompt}],
        }
        thread_data = CHAT_THREADS[message.channel.id]
    if not thread_data:
        await bot.process_commands(message)
        return
    if message.author.id != thread_data["user_id"]:
        return
    if message.content.strip().lower() in ["/close", "!close"]:
        del CHAT_THREADS[message.channel.id]
        await message.channel.send(embed=discord.Embed(title="✅ Chat closed", description="Use `/text` to start a new chat!", color=0x57F287))
        if isinstance(message.channel, discord.Thread):
            await message.channel.edit(archived=True, locked=True)
        return
    async with message.channel.typing():
        history = thread_data["history"]
        history.append({"role": "user", "content": message.content})
        try:
            # temporarily set provider to thread's original provider
            uid          = thread_data["user_id"]
            orig_prov    = USER_TEXT_PROVIDER.get(uid, "pollinations")
            thread_prov  = thread_data.get("provider", "pollinations")
            USER_TEXT_PROVIDER[uid] = thread_prov
            async with aiohttp.ClientSession() as session:
                reply, _ = await route_text(session, uid, history, thread_data.get("system", ""))
            USER_TEXT_PROVIDER[uid] = orig_prov
            if orig_prov == "pollinations":
                USER_TEXT_PROVIDER.pop(uid, None)
            history.append({"role": "assistant", "content": reply})
            for chunk in [reply[i:i+2000] for i in range(0, len(reply), 2000)]:
                await message.channel.send(chunk)
        except Exception as e:
            await message.channel.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245))


# ──────────────────────────────────────────────
#  ImageURLView
# ──────────────────────────────────────────────
class ImageURLView(discord.ui.View):
    def __init__(self, url: str):
        super().__init__(timeout=600)
        self._url = url
        self.add_item(discord.ui.Button(label="🔗 Open Image", style=discord.ButtonStyle.link, url=url, row=0))

    @discord.ui.button(label="📋 Copy URL", style=discord.ButtonStyle.secondary, row=0)
    async def copy_url_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"```\n{self._url}\n```", ephemeral=True)


# ──────────────────────────────────────────────
#  /image
# ──────────────────────────────────────────────
@bot.tree.command(name="image", description="Generate an image with AI")
@app_commands.describe(prompt="Describe the image", size="Image size")
@app_commands.choices(size=[
    app_commands.Choice(name="1024x1024 (square)",    value="1024x1024"),
    app_commands.Choice(name="1792x1024 (landscape)", value="1792x1024"),
    app_commands.Choice(name="1024x1792 (portrait)",  value="1024x1792"),
])
async def cmd_image(interaction: discord.Interaction, prompt: str, size: str = "1024x1024"):
    uid = interaction.user.id
    model_name = USER_MODELS.get(uid, {}).get("image", DEFAULT_MODELS["image"])
    if not is_free_model(model_name) and not has_personal_key(uid):
        await interaction.response.send_message(embed=paid_model_no_key_embed(model_name), ephemeral=True)
        return
    await interaction.response.defer(thinking=True)
    model = get_model(uid, "image")
    try:
        async with aiohttp.ClientSession() as session:
            w, h = size.split("x")
            seed = random.randint(1, 9999999)
            encoded = urllib.parse.quote(prompt)
            if has_personal_key(uid):
                img_url = f"https://gen.pollinations.ai/image/{encoded}?model={model}&width={w}&height={h}&nologo=true&seed={seed}"
                async with session.get(img_url, headers=auth_headers(get_key(uid))) as resp:
                    resp.raise_for_status(); img_bytes = await resp.read()
            else:
                img_url = f"https://image.pollinations.ai/prompt/{encoded}?model={model}&width={w}&height={h}&nologo=true&seed={seed}&nofeed=true"
                async with session.get(img_url) as resp:
                    resp.raise_for_status(); img_bytes = await resp.read()
        file  = discord.File(fp=io.BytesIO(img_bytes), filename="nov.png")
        embed = discord.Embed(color=BOT_COLOR)
        embed.set_author(name=f"🖼️ {model_name} - {size}")
        embed.set_image(url="attachment://nov.png")
        embed.set_footer(text=prompt[:100])
        await interaction.followup.send(embed=embed, file=file, view=ImageURLView(img_url))
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245))


# ──────────────────────────────────────────────
#  /audio
# ──────────────────────────────────────────────
@bot.tree.command(name="audio", description="Convert text to speech")
@app_commands.describe(text="Text to convert to audio")
async def cmd_audio(interaction: discord.Interaction, text: str):
    uid = interaction.user.id
    voice_name = USER_MODELS.get(uid, {}).get("audio", DEFAULT_MODELS["audio"])
    FREE_VOICES = ["Nova","Alloy","Echo","Fable","Onyx","Shimmer","Ash","Ballad","Coral","Sage","Verse",
                   "AssemblyAI Universal-2","Whisper Large V3","ACE-Step 1.5 Turbo","AssemblyAI Universal-3 Pro"]
    if voice_name not in FREE_VOICES and not has_personal_key(uid):
        await interaction.response.send_message(embed=not_logged_in_embed(), ephemeral=True)
        return
    await interaction.response.defer(thinking=True)
    voice = get_model(uid, "audio")
    try:
        async with aiohttp.ClientSession() as session:
            audio = await api_post_bytes(session, f"{BASE_URL}/audio/speech",
                                         {"model": "tts-1", "input": text, "voice": voice}, get_key(uid))
        file = discord.File(fp=io.BytesIO(audio), filename="nov_audio.mp3")
        await interaction.followup.send(
            content=f"🔊 **{voice}** — *{text[:80]}{'...' if len(text)>80 else ''}*", file=file)
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245))


# ──────────────────────────────────────────────
#  /video
# ──────────────────────────────────────────────
@bot.tree.command(name="video", description="Generate a video with AI (requires Pollen credits)")
@app_commands.describe(prompt="Describe the video")
async def cmd_video(interaction: discord.Interaction, prompt: str):
    if not has_personal_key(interaction.user.id):
        await interaction.response.send_message(embed=no_key_embed(), ephemeral=True)
        return
    await interaction.response.defer(thinking=True)
    model = get_model(interaction.user.id, "video")
    try:
        async with aiohttp.ClientSession() as session:
            encoded = urllib.parse.quote(prompt)
            async with session.get(f"https://gen.pollinations.ai/video/{encoded}?model={model}",
                                   headers=auth_headers(get_key(interaction.user.id))) as resp:
                resp.raise_for_status(); vid_bytes = await resp.read()
        file = discord.File(fp=io.BytesIO(vid_bytes), filename="nov_video.mp4")
        embed = discord.Embed(color=BOT_COLOR)
        embed.set_author(name=f"🎬 {model}")
        embed.set_footer(text=prompt[:100])
        await interaction.followup.send(embed=embed, file=file)
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(
            title="❌ Video error",
            description=f"`{e}`\n\n💡 Requires Pollen credits at [enter.pollinations.ai](https://enter.pollinations.ai)",
            color=0xED4245))


# ──────────────────────────────────────────────
#  /model — provider-aware
# ──────────────────────────────────────────────
@bot.tree.command(name="model", description="Change the AI model (and switch active provider)")
@app_commands.describe(provider="Which provider", type="Generation type", name="Model name (autocomplete)")
@app_commands.choices(provider=PROVIDER_CHOICES)
@app_commands.choices(type=[
    app_commands.Choice(name="💬 Text",  value="text"),
    app_commands.Choice(name="🖼️ Image", value="image"),
    app_commands.Choice(name="🔊 Audio", value="audio"),
    app_commands.Choice(name="🎬 Video", value="video"),
])
@app_commands.autocomplete(name=provider_model_autocomplete)
async def cmd_model(interaction: discord.Interaction, type: str, name: str, provider: str = "pollinations"):
    uid = interaction.user.id
    p   = PROVIDERS[provider]

    if provider == "pollinations":
        if not has_personal_key(uid):
            await interaction.response.send_message(embed=not_logged_in_embed(), ephemeral=True); return
        if not is_valid_model(type, name):
            await interaction.response.send_message(embed=invalid_model_embed(type, name, uid), ephemeral=True); return
        if not is_free_model(name) and not has_personal_key(uid):
            await interaction.response.send_message(embed=paid_model_no_key_embed(name), ephemeral=True); return
        if uid not in USER_MODELS:
            USER_MODELS[uid] = dict(DEFAULT_MODELS)
        prev = USER_MODELS[uid].get(type, DEFAULT_MODELS[type])
        USER_MODELS[uid][type] = name
        if type == "text":
            USER_TEXT_PROVIDER.pop(uid, None)
        embed = discord.Embed(title="✅ Pollinations model updated", color=0x57F287)
        embed.add_field(name="Type",   value=f"{TYPE_EMOJI[type]} {type}", inline=True)
        embed.add_field(name="Before", value=f"`{prev}`",                  inline=True)
        embed.add_field(name="Now",    value=f"`{name}`",                  inline=True)
        if "(PAID)" in name:
            embed.add_field(name="⚠️ Note",
                value="This model requires Pollen credits at [enter.pollinations.ai](https://enter.pollinations.ai)",
                inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if not is_provider_connected(uid, provider):
        await interaction.response.send_message(embed=provider_not_connected_embed(provider), ephemeral=True); return
    valid = PROVIDER_MODELS.get(provider, {}).get(type, [])
    if name not in valid:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Unknown model",
                description=f"`{name}` not in **{p['name']}** {type} models.\n\n**Available:**\n" +
                            "\n".join(f"`{m}`" for m in valid),
                color=0xED4245), ephemeral=True); return
    prev = get_provider_model(uid, provider, type)
    set_provider_model(uid, provider, type, name)
    if type == "text":
        USER_TEXT_PROVIDER[uid] = provider
    embed = discord.Embed(title="✅ Model updated", color=0x57F287)
    embed.add_field(name="Provider", value=f"{p['emoji']} {p['name']}", inline=True)
    embed.add_field(name="Type",     value=f"{TYPE_EMOJI.get(type,type)} {type}", inline=True)
    embed.add_field(name="Before",   value=f"`{prev or 'default'}`", inline=True)
    embed.add_field(name="Now",      value=f"`{name}`",              inline=True)
    if type == "text":
        embed.add_field(name="🔁 Active provider", value=f"Switched to **{p['name']}**", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ──────────────────────────────────────────────
#  /models
# ──────────────────────────────────────────────
@bot.tree.command(name="models", description="List available models")
@app_commands.describe(provider="Filter by provider")
@app_commands.choices(provider=PROVIDER_CHOICES)
async def cmd_models(interaction: discord.Interaction, provider: str = "pollinations"):
    uid = interaction.user.id
    if provider == "pollinations":
        if not has_personal_key(uid):
            embed = discord.Embed(title="📋 Nov - Available Models", description="🔓 *Free models only — `/connect` to unlock all*", color=BOT_COLOR)
            for t in ["text", "image"]:
                embed.add_field(name=f"{TYPE_EMOJI[t]} {t.capitalize()}", value="\n".join(f"`{m}`" for m in FREE_MODELS_NO_AUTH.get(t,[])) or "*none*", inline=False)
            embed.add_field(name="🔊 Audio (TTS voices)", value="\n".join(f"`{v}`" for v in ["Nova","Alloy","Echo","Fable","Onyx","Shimmer","Ash","Ballad","Coral","Sage","Verse"]), inline=False)
            embed.add_field(name="🎬 Video", value="🔒 Requires account — `/connect`", inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True); return
        embed = discord.Embed(title="📋 Pollinations — Models", color=BOT_COLOR)
        for t in ["text","image","audio","video"]:
            chunk_str, chunk_num = "", 1
            for m in KNOWN_MODELS[t]:
                line = f"`{m}`\n"
                if len(chunk_str)+len(line) > 1000:
                    embed.add_field(name=f"{TYPE_EMOJI[t]} {t.capitalize()}" + (f" ({chunk_num})" if chunk_num>1 else ""), value=chunk_str.strip(), inline=False)
                    chunk_str = line; chunk_num += 1
                else:
                    chunk_str += line
            if chunk_str:
                embed.add_field(name=f"{TYPE_EMOJI[t]} {t.capitalize()}" + (f" ({chunk_num})" if chunk_num>1 else ""), value=chunk_str.strip(), inline=False)
        embed.set_footer(text="(PAID) = requires Pollen credits • /model to change")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        p = PROVIDERS[provider]
        embed = discord.Embed(title=f"📋 {p['emoji']} {p['name']} — Models", color=BOT_COLOR)
        for t, models in PROVIDER_MODELS.get(provider, {}).items():
            embed.add_field(name=f"{TYPE_EMOJI.get(t,t)} {t.capitalize()}", value="\n".join(f"`{m}`" for m in models) or "*none*", inline=False)
        embed.set_footer(text=f"/model provider:{provider} type:text [name] to select")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ──────────────────────────────────────────────
#  /info
# ──────────────────────────────────────────────
@bot.tree.command(name="info", description="Show your current Nov settings")
async def cmd_info(interaction: discord.Interaction):
    uid    = interaction.user.id
    models = USER_MODELS.get(uid, DEFAULT_MODELS)
    mem    = get_memory(uid)
    embed  = discord.Embed(title="⚙️ Nov — Your Settings", color=BOT_COLOR)
    active = get_active_provider(uid)
    p = PROVIDERS[active]
    embed.add_field(name="🔁 Active Text Provider", value=f"{p['emoji']} **{p['name']}**", inline=False)
    if USER_KEYS.get(uid):
        k = USER_KEYS[uid]; embed.add_field(name="🌸 Pollinations", value=f"`{k[:6]}{'•'*(len(k)-9)}{k[-3:]}` ✅", inline=True)
    else:
        embed.add_field(name="🌸 Pollinations", value="❌ `/connect`", inline=True)
    for pid in ["openai","anthropic","gemini","llm7","mistral","xai"]:
        if pid in USER_PROVIDER_KEYS.get(uid, {}):
            k = USER_PROVIDER_KEYS[uid][pid]; pp = PROVIDERS[pid]
            embed.add_field(name=f"{pp['emoji']} {pp['name']}", value=f"`{k[:4]}{'•'*max(0,len(k)-7)}{k[-3:]}` ✅", inline=True)
    if active == "pollinations":
        for tipo in ["text","image","audio","video"]:
            embed.add_field(name=f"{TYPE_EMOJI[tipo]} {tipo.capitalize()}", value=f"`{models.get(tipo, DEFAULT_MODELS[tipo])}`", inline=True)
    else:
        embed.add_field(name="💬 Text Model", value=f"`{get_provider_model(uid, active, 'text') or 'default'}`", inline=True)
    if mem:
        embed.add_field(name="🧠 Memory", value="\n".join(f"**{k}:** {v}" for k,v in mem.items()), inline=False)
    embed.set_footer(text=f"Nov v{BOT_VERSION} · /connect to add providers")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ──────────────────────────────────────────────
#  /privtext
# ──────────────────────────────────────────────
@bot.tree.command(name="privtext", description="Open a private AI chat thread (only you and Nov can see it)")
@app_commands.describe(prompt="Your first message", system="Optional custom system prompt")
async def cmd_privtext(interaction: discord.Interaction, prompt: str, system: str = ""):
    in_guild   = interaction.guild is not None and isinstance(interaction.channel, discord.TextChannel)
    uid        = interaction.user.id
    provider   = get_active_provider(uid)
    sys_prompt = build_system_prompt(uid, system, interaction.guild_id)
    await interaction.response.defer(thinking=True, ephemeral=in_guild)
    try:
        messages = [{"role":"system","content":sys_prompt},{"role":"user","content":prompt}]
        async with aiohttp.ClientSession() as session:
            reply, model_label = await route_text(session, uid, messages, sys_prompt)
        if in_guild:
            target = await interaction.channel.create_thread(
                name=f"🔒 Nov · {interaction.user.display_name} · {prompt[:35]}",
                type=discord.ChannelType.private_thread, invitable=False, auto_archive_duration=60)
            await target.add_user(interaction.user)
            intro = discord.Embed(description=f"🔒 **Private thread**\n\n**You:** {prompt}", color=0x2B2D31)
            intro.set_author(name=f"Nov Chat (Private) — {model_label}")
            await target.send(embed=intro)
        else:
            intro = discord.Embed(description=f"🔒 **Private chat**\n\n**You:** {prompt}", color=0x2B2D31)
            intro.set_author(name=f"Nov Chat (Private) — {model_label}")
            await interaction.followup.send(embed=intro)
            target = interaction.channel
        for chunk in [reply[i:i+2000] for i in range(0, len(reply), 2000)]:
            await target.send(chunk)
        CHAT_THREADS[target.id] = {
            "user_id":uid,"provider":provider,"system":sys_prompt,"private":True,
            "history":[{"role":"system","content":sys_prompt},{"role":"user","content":prompt},{"role":"assistant","content":reply}],
        }
        if in_guild:
            await interaction.followup.send(f"🔒 Private thread opened! → {target.mention}", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send(embed=discord.Embed(title="❌ Missing permissions",
            description="Nov can't create private threads here. Check Community and Private Threads permission.",
            color=0xED4245), ephemeral=True)
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245), ephemeral=True)


# ──────────────────────────────────────────────
#  /ping
# ──────────────────────────────────────────────
@bot.tree.command(name="ping", description="Check Nov's latency")
async def cmd_ping(interaction: discord.Interaction):
    t_start = time.monotonic()
    await interaction.response.defer(thinking=True)
    api_ms = round((time.monotonic() - t_start) * 1000)
    ws_ms  = round(bot.latency * 1000)
    def colored_bar(ms):
        filled = min(10, max(1, ms // 30))
        return ("🟢" if ms<100 else "🟡" if ms<200 else "🔴"), "█"*filled+"░"*(10-filled)
    ws_e, ws_bar   = colored_bar(ws_ms)
    api_e, api_bar = colored_bar(api_ms)
    embed = discord.Embed(title="🏓 Pong!", color=BOT_COLOR)
    embed.add_field(name="WebSocket",      value=f"{ws_e} `{ws_bar}` **{ws_ms} ms**",  inline=False)
    embed.add_field(name="API Round-trip", value=f"{api_e} `{api_bar}` **{api_ms} ms**", inline=False)
    embed.set_footer(text="🟢 <100ms  🟡 100–200ms  🔴 >200ms")
    await interaction.followup.send(embed=embed)


# ──────────────────────────────────────────────
#  /ask
# ──────────────────────────────────────────────
@bot.tree.command(name="ask", description="Get an instant AI reply without opening a thread")
@app_commands.describe(prompt="Your question or request")
async def cmd_ask(interaction: discord.Interaction, prompt: str):
    uid      = interaction.user.id
    provider = get_active_provider(uid)
    if provider == "pollinations":
        model_name = USER_MODELS.get(uid, {}).get("text", DEFAULT_MODELS["text"])
        if not is_free_model(model_name) and not has_personal_key(uid):
            await interaction.response.send_message(embed=paid_model_no_key_embed(model_name), ephemeral=True); return
    await interaction.response.defer(thinking=True)
    sys_prompt = build_system_prompt(uid, "", interaction.guild_id)
    messages   = [{"role":"system","content":sys_prompt},{"role":"user","content":prompt}]
    try:
        async with aiohttp.ClientSession() as session:
            reply, model_label = await route_text(session, uid, messages, sys_prompt, max_tokens=1000)
        embed = discord.Embed(description=reply[:4096], color=BOT_COLOR)
        embed.set_author(name=f"💬 {model_label}")
        embed.set_footer(text=f"Quick reply for {interaction.user.display_name} • /text for full chat")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245))


# ──────────────────────────────────────────────
#  /translate
# ──────────────────────────────────────────────
@bot.tree.command(name="translate", description="Translate text into any language using the active text model")
@app_commands.describe(text="Text to translate", language="Target language (e.g. Italian, Japanese, French)")
async def cmd_translate(interaction: discord.Interaction, text: str, language: str):
    uid        = interaction.user.id
    await interaction.response.defer(thinking=True)
    sys_prompt = (f"You are a professional translator. Translate the following text into {language}. "
                  "Output ONLY the translation — no explanations, no preamble.")
    messages   = [{"role":"system","content":sys_prompt},{"role":"user","content":text}]
    try:
        async with aiohttp.ClientSession() as session:
            result, model_label = await route_text(session, uid, messages, sys_prompt, max_tokens=1000)
        embed = discord.Embed(color=BOT_COLOR)
        embed.set_author(name=f"🌐 Translation → {language}")
        embed.add_field(name="🔤 Original",    value=text[:1000],   inline=False)
        embed.add_field(name=f"🌐 {language}", value=result[:1000], inline=False)
        embed.set_footer(text=f"Model: {model_label}")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245))


# ──────────────────────────────────────────────
#  /summarize
# ──────────────────────────────────────────────
@bot.tree.command(name="summarize", description="Summarize text in 4 different styles")
@app_commands.describe(text="Text to summarize", style="Summary style")
@app_commands.choices(style=[
    app_commands.Choice(name="• Bullet points", value="bullet"),
    app_commands.Choice(name="📄 Paragraph",    value="paragraph"),
    app_commands.Choice(name="1️⃣ One sentence", value="sentence"),
    app_commands.Choice(name="📢 TL;DR",        value="tldr"),
])
async def cmd_summarize(interaction: discord.Interaction, text: str, style: str = "bullet"):
    uid = interaction.user.id
    await interaction.response.defer(thinking=True)
    STYLE_PROMPTS = {
        "bullet":    "Summarize the following text as a concise bullet point list. Use • for each bullet.",
        "paragraph": "Summarize the following text in a single coherent paragraph.",
        "sentence":  "Summarize the following text in exactly one sentence. Nothing else.",
        "tldr":      "Write a TL;DR summary of the following text. Start with 'TL;DR:'",
    }
    STYLE_LABELS = {"bullet":"• Bullet Points","paragraph":"📄 Paragraph","sentence":"1️⃣ One Sentence","tldr":"📢 TL;DR"}
    sys_prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["bullet"])
    messages   = [{"role":"system","content":sys_prompt},{"role":"user","content":text}]
    try:
        async with aiohttp.ClientSession() as session:
            result, model_label = await route_text(session, uid, messages, sys_prompt, max_tokens=800)
        embed = discord.Embed(title=f"📝 Summary — {STYLE_LABELS.get(style,style)}", description=result[:4096], color=BOT_COLOR)
        embed.set_footer(text=f"Model: {model_label}")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245))


# ──────────────────────────────────────────────
#  /poll
# ──────────────────────────────────────────────
@bot.tree.command(name="poll", description="AI generates a poll question with 4 options and auto-adds reactions")
@app_commands.describe(topic="Poll topic")
async def cmd_poll(interaction: discord.Interaction, topic: str):
    uid = interaction.user.id
    await interaction.response.defer(thinking=True)
    sys_prompt = ('You are a poll generator. Given a topic, create a fun poll question with exactly 4 short options. '
                  'Respond ONLY with valid JSON: {"question":"...","options":["...","...","...","..."]}')
    messages   = [{"role":"system","content":sys_prompt},{"role":"user","content":f"Create a poll about: {topic}"}]
    try:
        async with aiohttp.ClientSession() as session:
            raw, _ = await route_text(session, uid, messages, sys_prompt, max_tokens=300)
        poll_data = json.loads(raw.strip().strip("```json").strip("```").strip())
        question  = poll_data["question"]
        options   = poll_data["options"][:4]
        letters   = ["🇦","🇧","🇨","🇩"]
        desc      = f"**{question}**\n\n" + "".join(f"{letters[i]} {opt}\n" for i,opt in enumerate(options))
        embed     = discord.Embed(title="📊 Poll", description=desc, color=BOT_COLOR)
        embed.set_footer(text=f"React to vote! • Topic: {topic[:60]}")
        msg = await interaction.followup.send(embed=embed)
        for letter in letters[:len(options)]:
            await msg.add_reaction(letter)
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Poll error", description=f"`{e}`", color=0xED4245))


# ──────────────────────────────────────────────
#  /roast
# ──────────────────────────────────────────────
@bot.tree.command(name="roast", description="Get a harmless but spicy AI roast 🔥")
@app_commands.describe(target="Who (or what) to roast")
async def cmd_roast(interaction: discord.Interaction, target: str):
    uid = interaction.user.id
    await interaction.response.defer(thinking=True)
    sys_prompt = ("You are a comedy roast master. Write a short, funny, and harmless roast — purely playful, "
                  "no hate speech, no slurs. Keep it to 3–4 sentences max.")
    messages   = [{"role":"system","content":sys_prompt},{"role":"user","content":f"Roast: {target}"}]
    try:
        async with aiohttp.ClientSession() as session:
            roast, _ = await route_text(session, uid, messages, sys_prompt, max_tokens=300)
        embed = discord.Embed(title=f"🔥 Roasting: {target}", description=roast, color=0xFF4500)
        embed.set_footer(text=f"Requested by {interaction.user.display_name} • all in good fun 😄")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245))


# ──────────────────────────────────────────────
#  /batch
# ──────────────────────────────────────────────
@bot.tree.command(name="batch", description="Generate multiple image variations in parallel")
@app_commands.describe(prompt="Image description", count="Number of variations (2–4)")
@app_commands.choices(count=[
    app_commands.Choice(name="2 images", value=2),
    app_commands.Choice(name="3 images", value=3),
    app_commands.Choice(name="4 images", value=4),
])
async def cmd_batch(interaction: discord.Interaction, prompt: str, count: int = 2):
    uid        = interaction.user.id
    model_name = USER_MODELS.get(uid, {}).get("image", DEFAULT_MODELS["image"])
    if not is_free_model(model_name) and not has_personal_key(uid):
        await interaction.response.send_message(embed=paid_model_no_key_embed(model_name), ephemeral=True); return
    await interaction.response.defer(thinking=True)
    model   = get_model(uid, "image")
    encoded = urllib.parse.quote(prompt)
    def make_url(seed):
        if has_personal_key(uid):
            return f"https://gen.pollinations.ai/image/{encoded}?model={model}&width=1024&height=1024&nologo=true&seed={seed}"
        return f"https://image.pollinations.ai/prompt/{encoded}?model={model}&width=1024&height=1024&nologo=true&seed={seed}&nofeed=true"
    async def fetch_one(session, url):
        if has_personal_key(uid):
            async with session.get(url, headers=auth_headers(get_key(uid))) as resp:
                resp.raise_for_status(); return await resp.read()
        async with session.get(url) as resp:
            resp.raise_for_status(); return await resp.read()
    try:
        seeds   = [random.randint(1, 9_999_999) for _ in range(count)]
        urls    = [make_url(s) for s in seeds]
        async with aiohttp.ClientSession() as session:
            results = await asyncio.gather(*[fetch_one(session, u) for u in urls], return_exceptions=True)
        good = [(i,r,urls[i]) for i,r in enumerate(results) if not isinstance(r, Exception)]
        if not good: raise Exception("All generations failed")
        files = [discord.File(fp=io.BytesIO(r), filename=f"nov_batch_{i+1}.png") for i,r,_ in good]
        class BatchURLView(discord.ui.View):
            def __init__(self, image_urls):
                super().__init__(timeout=600)
                self._all = "\n".join(f"**#{i+1}** `{u}`" for i,u in enumerate(image_urls))
                for idx,u in enumerate(image_urls):
                    self.add_item(discord.ui.Button(label=f"🔗 #{idx+1}", style=discord.ButtonStyle.link, url=u, row=0))
            @discord.ui.button(label="📋 Copy All URLs", style=discord.ButtonStyle.secondary, row=1)
            async def copy_all(self, interaction, button):
                await interaction.response.send_message(self._all, ephemeral=True)
        embed = discord.Embed(title=f"🖼️ Batch — {len(good)}/{count} generated", description=f"**Prompt:** {prompt[:200]}", color=BOT_COLOR)
        embed.set_footer(text=f"Model: {model_name} • {count} parallel variations")
        await interaction.followup.send(embed=embed, files=files, view=BatchURLView([u for _,_,u in good]))
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Batch error", description=f"`{e}`", color=0xED4245))


# ──────────────────────────────────────────────
#  /edit
# ──────────────────────────────────────────────
@bot.tree.command(name="edit", description="Edit an image with FLUX.1 Kontext (requires account)")
@app_commands.describe(image_url="URL of the source image", prompt="What to change in the image")
async def cmd_edit(interaction: discord.Interaction, image_url: str, prompt: str):
    uid = interaction.user.id
    if not has_personal_key(uid):
        await interaction.response.send_message(embed=not_logged_in_embed(), ephemeral=True); return
    await interaction.response.defer(thinking=True)
    try:
        seed     = random.randint(1, 9_999_999)
        edit_url = (f"https://gen.pollinations.ai/image/{urllib.parse.quote(prompt)}"
                    f"?model=kontext&input_image={urllib.parse.quote(image_url)}&nologo=true&seed={seed}")
        async with aiohttp.ClientSession() as session:
            async with session.get(edit_url, headers=auth_headers(get_key(uid))) as resp:
                resp.raise_for_status(); img_bytes = await resp.read()
        file  = discord.File(fp=io.BytesIO(img_bytes), filename="nov_edit.png")
        embed = discord.Embed(color=BOT_COLOR)
        embed.set_author(name="✏️ FLUX.1 Kontext — Image Edit")
        embed.add_field(name="Edit prompt", value=prompt[:500], inline=False)
        embed.set_image(url="attachment://nov_edit.png")
        await interaction.followup.send(embed=embed, file=file, view=ImageURLView(edit_url))
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Edit error",
            description=f"`{e}`\n\n💡 Make sure the image URL is publicly accessible.", color=0xED4245))


# ──────────────────────────────────────────────
#  /reset
# ──────────────────────────────────────────────
@bot.tree.command(name="reset", description="Close and archive this chat thread (owner only)")
async def cmd_reset(interaction: discord.Interaction):
    ch          = interaction.channel
    thread_data = CHAT_THREADS.get(ch.id)
    if not thread_data:
        await interaction.response.send_message(embed=discord.Embed(title="❌ Not in a Nov thread", description="Use this command inside an active Nov chat thread.", color=0xED4245), ephemeral=True); return
    if thread_data["user_id"] != interaction.user.id:
        await interaction.response.send_message(embed=discord.Embed(title="🔒 Not your thread", description="Only the thread owner can reset it.", color=0xFEE75C), ephemeral=True); return
    del CHAT_THREADS[ch.id]
    await interaction.response.send_message(embed=discord.Embed(title="🗑️ Thread closed", description="This chat session has been ended.", color=0x57F287))
    if isinstance(ch, discord.Thread):
        try: await ch.edit(archived=True, locked=True)
        except Exception: pass


# ──────────────────────────────────────────────
#  /export
# ──────────────────────────────────────────────
@bot.tree.command(name="export", description="Download this thread's chat history as a .txt file")
async def cmd_export(interaction: discord.Interaction):
    ch          = interaction.channel
    thread_data = CHAT_THREADS.get(ch.id)
    if not thread_data:
        await interaction.response.send_message(embed=discord.Embed(title="❌ Not in a Nov thread", color=0xED4245), ephemeral=True); return
    history = thread_data.get("history", [])
    lines   = [f"Nov Chat Export — {interaction.user.display_name}\n", "="*50+"\n\n"]
    for msg in history:
        if msg["role"] == "system": continue
        lines.append(f"[{msg['role'].upper()}]\n{msg['content']}\n\n")
    file = discord.File(fp=io.BytesIO("".join(lines).encode("utf-8")), filename="nov_chat_export.txt")
    await interaction.response.send_message(content="📄 Here's your chat history:", file=file, ephemeral=True)


# ──────────────────────────────────────────────
#  /profile
# ──────────────────────────────────────────────
@bot.tree.command(name="profile", description="View your Pollinations profile (requires account)")
async def cmd_profile(interaction: discord.Interaction):
    uid = interaction.user.id
    if not has_personal_key(uid):
        await interaction.response.send_message(embed=not_logged_in_embed(), ephemeral=True); return
    await interaction.response.defer(thinking=True, ephemeral=True)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{AUTH_URL}/userinfo", headers={"Authorization": f"Bearer {get_key(uid)}"}) as resp:
                resp.raise_for_status(); ui = await resp.json()
        embed = discord.Embed(title="👤 Your Pollinations Profile", color=BOT_COLOR)
        embed.add_field(name="🐙 GitHub", value=f"`{ui.get('github_username') or ui.get('preferred_username','?')}`", inline=True)
        embed.add_field(name="⚡ Tier",   value=f"`{ui.get('tier','Free')}`", inline=True)
        embed.add_field(name="🌸 Pollen", value=f"`{ui.get('pollen_balance') or ui.get('balance','N/A')}`", inline=True)
        embed.set_footer(text="enter.pollinations.ai • manage your account online")
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245), ephemeral=True)


# ──────────────────────────────────────────────
#  /privchat
# ──────────────────────────────────────────────
@bot.tree.command(name="privchat", description="Open a private thread with Nov (no message needed)")
async def cmd_privchat(interaction: discord.Interaction):
    uid      = interaction.user.id
    provider = get_active_provider(uid)
    p        = PROVIDERS[provider]
    in_guild = interaction.guild is not None and isinstance(interaction.channel, discord.TextChannel)
    await interaction.response.defer(thinking=True, ephemeral=in_guild)
    sys_prompt  = build_system_prompt(uid, "", interaction.guild_id)
    bot_display = get_server_name(interaction.guild_id)
    try:
        if in_guild:
            thread = await interaction.channel.create_thread(
                name=f"🔒 {bot_display} · {interaction.user.display_name}",
                type=discord.ChannelType.private_thread, invitable=False, auto_archive_duration=60)
            await thread.add_user(interaction.user)
            intro = discord.Embed(description=f"🔒 **Private chat started**\n\nHey {interaction.user.display_name}! 👋\nJust type here. Use `/reset` to end.", color=0x2B2D31)
            intro.set_author(name=f"{bot_display} Chat (Private) — {p['emoji']} {p['name']}")
            await thread.send(embed=intro)
            CHAT_THREADS[thread.id] = {"user_id":uid,"provider":provider,"system":sys_prompt,"private":True,"history":[{"role":"system","content":sys_prompt}]}
            await interaction.followup.send(f"🔒 Private thread opened! → {thread.mention}", ephemeral=True)
        else:
            intro = discord.Embed(description=f"🔒 **Private chat started**\n\nHey {interaction.user.display_name}! 👋\nJust type here. Use `/reset` to end.", color=0x2B2D31)
            intro.set_author(name=f"{bot_display} Chat (Private) — {p['emoji']} {p['name']}")
            await interaction.followup.send(embed=intro)
            CHAT_THREADS[interaction.channel.id] = {"user_id":uid,"provider":provider,"system":sys_prompt,"private":True,"history":[{"role":"system","content":sys_prompt}]}
    except discord.Forbidden:
        await interaction.followup.send(embed=discord.Embed(title="❌ Missing permissions",
            description="Check Community mode and Private Threads permission.", color=0xED4245), ephemeral=True)
    except Exception as e:
        await interaction.followup.send(embed=discord.Embed(title="❌ Error", description=f"`{e}`", color=0xED4245), ephemeral=True)


# ──────────────────────────────────────────────
#  /globalidentity / /resetidentity
# ──────────────────────────────────────────────
@bot.tree.command(name="globalidentity", description="Give NovAI a custom name & personality in this server")
@app_commands.describe(name="Bot name for this server", personality="Custom personality")
async def cmd_globalidentity(interaction: discord.Interaction, name: str, personality: str):
    if not interaction.guild:
        await interaction.response.send_message(embed=discord.Embed(title="❌ Server only", color=0xED4245), ephemeral=True); return
    gid = interaction.guild.id
    if gid in SERVER_IDENTITY and SERVER_IDENTITY[gid]["owner_id"] != interaction.user.id:
        await interaction.response.send_message(embed=discord.Embed(
            title="🔒 Identity already set",
            description=f"Already set to **{SERVER_IDENTITY[gid]['name']}** by <@{SERVER_IDENTITY[gid]['owner_id']}>.",
            color=0xFEE75C), ephemeral=True); return
    SERVER_IDENTITY[gid] = {"name": name[:32].strip(), "personality": personality[:500].strip(), "owner_id": interaction.user.id}
    await interaction.response.send_message(embed=discord.Embed(
        title=f"✅ Identity set — {name}",
        description=f"NovAI will answer as **{name}** in this server.\n\n**Personality:**\n> {personality[:280]}",
        color=0x57F287).set_footer(text=f"Set by {interaction.user.display_name}"))

@bot.tree.command(name="resetidentity", description="Reset NovAI's custom server identity")
async def cmd_resetidentity(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message(embed=discord.Embed(title="❌ Server only", color=0xED4245), ephemeral=True); return
    gid = interaction.guild.id
    if gid not in SERVER_IDENTITY:
        await interaction.response.send_message(embed=discord.Embed(title="ℹ️ No custom identity", color=BOT_COLOR), ephemeral=True); return
    if SERVER_IDENTITY[gid]["owner_id"] != interaction.user.id:
        await interaction.response.send_message(embed=discord.Embed(title="🔒 Not authorized",
            description=f"Only <@{SERVER_IDENTITY[gid]['owner_id']}> can reset this.", color=0xED4245), ephemeral=True); return
    old = SERVER_IDENTITY.pop(gid)["name"]
    await interaction.response.send_message(embed=discord.Embed(title="🔄 Identity reset", description=f"**{old}** removed.", color=0x57F287))


# ──────────────────────────────────────────────
#  /matrix
# ──────────────────────────────────────────────
_MATRIX_CHARS = list("アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン01234567890101110100101")

def _matrix_frame(cols=18, rows=9, reveal=""):
    mid = rows // 2
    lines = []
    for r in range(rows):
        if reveal and r == mid:
            msg  = reveal[:cols]; pad = (cols-len(msg))//2; side = cols-pad-len(msg)
            left  = "".join(random.choice(_MATRIX_CHARS) for _ in range(pad))
            right = "".join(random.choice(_MATRIX_CHARS) for _ in range(side))
            line  = f"\u001b[2;32m{left}\u001b[0m\u001b[1;37m {msg} \u001b[0m\u001b[2;32m{right}\u001b[0m"
        else:
            raw = "".join(random.choice(_MATRIX_CHARS) for _ in range(cols)); head = random.randint(0,cols-1); line = ""
            for i,ch in enumerate(raw):
                if i == head: line += f"\u001b[1;32m{ch}\u001b[0m"
                elif random.random() > 0.55: line += f"\u001b[32m{ch}\u001b[0m"
                else: line += f"\u001b[2;32m{ch}\u001b[0m"
        lines.append(line)
    return "```ansi\n" + "\n".join(lines) + "\n```"

@bot.tree.command(name="matrix", description="Display an animated Matrix rain in the channel 💚")
@app_commands.describe(message="Secret message to reveal at the end (optional)")
async def cmd_matrix(interaction: discord.Interaction, message: str = ""):
    await interaction.response.defer()
    reveal_text = message.strip()[:16] if message.strip() else "SYSTEM ONLINE"
    msg = await interaction.followup.send(_matrix_frame())
    for _ in range(4):
        await asyncio.sleep(0.85)
        try: await msg.edit(content=_matrix_frame())
        except Exception: break
    await asyncio.sleep(0.85)
    caption = f"\n-# 🔓 `{reveal_text}`" if message.strip() else "\n-# 💚 Wake up, Neo…"
    try: await msg.edit(content=_matrix_frame(reveal=reveal_text) + caption)
    except Exception: pass


# ──────────────────────────────────────────────
#  /event
# ──────────────────────────────────────────────
@bot.tree.command(name="event", description="Create an AI-powered event announcement 🎉")
@app_commands.describe(title="Event name", date="When?", details="Extra details (optional)")
async def cmd_event(interaction: discord.Interaction, title: str, date: str, details: str = ""):
    await interaction.response.defer(thinking=True)
    uid = interaction.user.id; key = get_key(uid)
    ai_prompt = (f"Write a hype Discord event announcement for '{title}' happening on {date}. "
                 f"{'Additional details: '+details if details else ''} "
                 "Make it enthusiastic, 2-3 emojis, max 120 words. Return ONLY the announcement text.")
    try:
        async with aiohttp.ClientSession() as session:
            data    = await api_post_json(session, f"{BASE_URL}/chat/completions",
                                          {"model":"openai","messages":[{"role":"user","content":ai_prompt}],"max_tokens":220}, key)
        ai_text = data["choices"][0]["message"]["content"].strip()
    except Exception:
        ai_text = details or "Join us for this special event!"
    colors = [0x5865F2,0xFEE75C,0x57F287,0xEB459E,0xED4245]
    embed  = discord.Embed(title=f"📅  {title}", description=ai_text, color=random.choice(colors))
    embed.add_field(name="🗓️ When", value=f"`{date}`", inline=True)
    embed.add_field(name="📢 Host", value=interaction.user.mention, inline=True)
    if interaction.guild: embed.add_field(name="📍 Where", value=interaction.guild.name, inline=True)
    embed.set_footer(text="React below if you're coming! ✅ = yes · ❌ = no · 🤔 = maybe")
    followup_msg = await interaction.followup.send(embed=embed)
    for emoji in ["✅","❌","🤔"]:
        try: await followup_msg.add_reaction(emoji)
        except Exception: pass


# ──────────────────────────────────────────────
#  /help
# ──────────────────────────────────────────────
@bot.tree.command(name="help", description="Show all Nov commands")
async def cmd_help(interaction: discord.Interaction):
    embed = discord.Embed(title="✨ Nov — Commands", description="AI-powered bot · Multi-Provider Edition", color=BOT_COLOR)
    embed.add_field(name="🔑 Providers",
        value=("`/connect [provider]` · Link any AI provider\n"
               "`/disconnect [provider]` · Remove a provider\n"
               "`/info` · View your settings & active provider\n"
               "`/profile` · Pollinations tier & balance\n\n"
               "**Available:** 🌸 Pollinations · 🟢 OpenAI · 🟠 Anthropic · 🔵 Gemini · 🌐 LLM7 · 🔴 Mistral · ⚫ xAI"), inline=False)
    embed.add_field(name="⚙️ Models",
        value=("`/model [provider] [type] [name]` · Set model & switch provider\n"
               "`/models [provider]` · List models for a provider"), inline=False)
    embed.add_field(name="🧠 Memory",
        value="`/remember [key] [value]` · Save info\n`/forget` · Clear memory", inline=False)
    embed.add_field(name="💬 Chat",
        value=("`/text` · Open AI chat thread (uses active provider)\n"
               "`/privtext` · 🔒 Private thread (with first message)\n"
               "`/privchat` · 🔒 Private thread (no message)\n"
               "`/ask [prompt]` · Instant reply, no thread\n"
               "`/reset` · Close & archive thread\n"
               "`/export` · Download chat history"), inline=False)
    embed.add_field(name="🖼️ Image / 🔊 Audio / 🎬 Video",
        value=("`/image [prompt]` · Generate image\n"
               "`/batch [prompt] [2-4]` · Multiple variations\n"
               "`/edit [url] [prompt]` · Edit with Kontext\n"
               "`/audio [text]` · Text to speech\n"
               "`/video [prompt]` · Generate video"), inline=False)
    embed.add_field(name="🛠️ Utilities",
        value=("`/ping` · Latency · `/translate` · `/summarize` · `/poll` · `/roast` · `/matrix` · `/event`"), inline=False)
    embed.add_field(name="🎭 Server Identity",
        value="`/globalidentity` · Custom name & persona\n`/resetidentity` · Revert to default", inline=False)
    embed.set_footer(text=f"Nov v{BOT_VERSION} · Works in DMs too! · Multi-Provider")
    await interaction.response.send_message(embed=embed)


# ──────────────────────────────────────────────
#  START
# ──────────────────────────────────────────────
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌  DISCORD_TOKEN missing in .env!"); exit(1)
    print(f"🚀  Starting {BOT_NAME} v{BOT_VERSION}...")
    bot.run(DISCORD_TOKEN)
