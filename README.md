# DuckDuckGo AI Bot

This is a Telegram bot that lets you chat with DuckDuckGo's AI models.

## Setup

1. Clone this repo
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Get a bot token from [@BotFather](https://t.me/BotFather) on Telegram
4. Put your token in `ddgai.py`
5. Run:
   ```bash
   python ddgai.py
   ```

## Commands

- `/start` - Start bot and pick a model
- `/model` - Change AI model

## Models Available

- Claude-3-haiku
- GPT-4o-mini  
- Meta-Llama-3.1
- Mixtral

## Live Demo

This bot is avaliable in Telegram: [@ddgairobot](https://t.me/ddgairobot)

## Note

Uses DuckDuckGo's chat API so might break if they change stuff.

For now, it uses mojoproxy.com to bypass the request limit. You can change it to any other proxy/remove it if you don't want to use it.


