<div align="center">

<img src="logo.png" width="120" alt="NovAI logo"/>

# NovAI

**AI-powered Discord bot — text, images, audio, and video generation**

[![Add to Discord](https://img.shields.io/badge/Add%20to%20Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com/oauth2/authorize?client_id=1520183989200093205&permissions=8&integration_type=0&scope=bot+applications.commands)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Nov-AI/NovAI)


</div>

---

## Overview

NovAI brings AI generation directly into your Discord server through slash commands. Generate text with dozens of models, create images, convert text to speech, and produce videos — all without leaving Discord.

No account required to get started. Connect your Pollinations account to unlock the full model catalogue and video generation.

---

## Commands

| Command | Description |
|---|---|
| `/text [prompt]` | Open a persistent AI chat thread |
| `/image [prompt]` | Generate an image |
| `/audio [text]` | Text to speech |
| `/video [prompt]` | Generate a video |
| `/model [type] [name]` | Switch AI model with autocomplete |
| `/models` | List all available models |
| `/connect` | Link your Pollinations account |
| `/disconnect` | Remove your linked account |
| `/remember [key] [value]` | Save info NovAI will remember about you |
| `/forget` | Clear your saved memory |
| `/info` | View your current settings |
| `/help` | Show all commands |

---

## Access Tiers

### Free — no account needed
- **Text** — 1 model, GPT-4o
- **Image** — Flux Schnell

### Full access — connect your Pollinations account

- All pollinations text generation models — GPT‑5.5, Gemini, Claude, Grok, Mistral, Llama, DeepSeek, and more

- All pollinations image generation models — Ideogram, Seedream, Grok Imagine, FLUX variants, and more

- All pollinations video generation models — Veo 3.1, LTX 2.3, Nova Reel,  Wan 3.7, and more

- BYOP — your Pollen credits cover your own usage

Use `/connect` to authorize via the [Pollinations device flow](https://enter.pollinations.ai/device).

---

## Self-Hosting

### Requirements

```
Python 3.11+
discord.py >= 2.3.0
aiohttp >= 3.9.0
python-dotenv >= 1.0.0
```

### Install

```bash
pip install discord.py aiohttp python-dotenv
```

### Setup

1. Create a bot at [discord.com/developers](https://discord.com/developers/applications)
2. Enable **Message Content Intent** under Bot → Privileged Gateway Intents
3. Create a `.env` file in the project root:

```env
DISCORD_TOKEN=your_discord_bot_token
```

### Run

```bash
python Bot.py
```

---

## Deploy on Any Hosting Platform (ex. Railway)

1. Push the repository to GitHub
2. Connect the repo to [Railway](https://railway.app)
3. Add `DISCORD_TOKEN` under **Variables**
4. Add a `Procfile`:

```
worker: python Bot.py
```

Railway will auto-deploy on every push to your main branch.

---

## BYOP — Bring Your Own Pollen

NovAI uses the [Pollinations device flow](https://enter.pollinations.ai) to let users authorize with their own account. When a user runs `/connect`, NovAI provides a short code to enter at `enter.pollinations.ai/device`. Once authorized, their own Pollen credits cover their usage — the server owner's credits are never touched.

---

## Stack

| | |
|---|---|
| [discord.py](https://discordpy.readthedocs.io) | Discord bot framework |
| [Pollinations AI](https://pollinations.ai) | Inference backend for all generation types |
| [aiohttp](https://docs.aiohttp.org) | Async HTTP client |
| [Railway](https://railway.app) | Hosting |

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

<div align="center">

*NovAI is an independent project and is not affiliated with Pollinations AI.*

</div>
