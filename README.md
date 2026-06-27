# NovAI

**AI for Discord — powered by [Pollinations AI](https://pollinations.ai)**

Generate text, images, audio, and video directly in your Discord server using slash commands.

---

## Commands

| Command | Description |
|---|---|
| `/connect` | Link your Pollinations account (BYOP device flow) |
| `/disconnect` | Remove your linked account |
| `/text [prompt]` | Open an AI chat thread — just type inside to keep chatting |
| `/image [prompt]` | Generate an image |
| `/audio [text]` | Text to speech |
| `/video [prompt]` | Generate a video (requires Pollen credits) |
| `/model [type] [name]` | Switch AI model with autocomplete |
| `/models` | List available models |
| `/remember [key] [value]` | Save info Nov will remember about you |
| `/forget` | Clear your saved memory |
| `/info` | View your current settings |
| `/help` | Show all commands |

---

## Without an account

Basic features work without a Pollinations account:

- `/text` — 12 free models (GPT-5.4 Nano default)
- `/image` — Flux Schnell only
- `/audio` — 11 OpenAI TTS voices (Nova, Alloy, Echo, Fable, Onyx, Shimmer, Ash, Ballad, Coral, Sage, Verse)

Use `/connect` to unlock all models, video generation, and paid models.

---

## Self-hosting

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
2. Enable **Message Content Intent** under Bot settings
3. Get your API key at [enter.pollinations.ai](https://enter.pollinations.ai)
4. Create a `.env` file:

```env
DISCORD_TOKEN=your_discord_bot_token
```

### Run

```bash
python Bot.py
```

### Deploy on Railway

1. Push to a GitHub repo
2. Connect repo to [Railway](https://railway.app)
3. Add `DISCORD_TOKEN` in Railway → Variables
4. Add a `Procfile`:

```
worker: python Bot.py
```

---

## BYOP — Bring Your Own Pollen

Nov uses the [Pollinations Device Flow](https://enter.pollinations.ai) to let users authorize with their own account. When a user runs `/connect`, Nov gives them a short code to enter at `enter.pollinations.ai/device`. Once authorized, their own Pollen credits cover their usage.

---

## Stack

- [discord.py](https://discordpy.readthedocs.io) — Discord bot framework
- [Pollinations AI](https://pollinations.ai) — inference backend
- [Railway](https://railway.app) — hosting

---

*Nov is not affiliated with Pollinations AI.*
