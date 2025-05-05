import json
import yaml
import os
import asyncio
from telegram import Bot
from telegram.constants import ParseMode
from rich import print

GUARDIAN_JSON = "guardian_memory.json"
GUARDIAN_YAML = "guardian_memory.yaml"

def load_guardian_memory():
    memory = {}

    if os.path.exists(GUARDIAN_JSON):
        with open(GUARDIAN_JSON, 'r') as f:
            try:
                memory.update(json.load(f))
                print("[green]Loaded guardian_memory.json[/green]")
            except Exception as e:
                print(f"[red]Error loading JSON:[/red] {e}")

    if os.path.exists(GUARDIAN_YAML):
        with open(GUARDIAN_YAML, 'r') as f:
            try:
                memory.update(yaml.safe_load(f))
                print("[blue]Loaded guardian_memory.yaml[/blue]")
            except Exception as e:
                print(f"[red]Error loading YAML:[/red] {e}")

    if not memory:
        print("[yellow]No memory files loaded. Please check paths.[/yellow]")

    return memory

async def send_telegram_alert(msg):
    bot = Bot(token="8152119100:AAHMMPWwN9iaILOLxLBtvcgIwEtsRalGVUY")
    await bot.send_message(chat_id="8039598369", text=f"✅ {msg}", parse_mode=ParseMode.HTML)

def guardian_brain():
    brain = load_guardian_memory()
    print("[bold green]Guardian memory loaded.[/bold green]")
    print(brain)
    asyncio.run(send_telegram_alert("Guardian has launched and is online."))

if __name__ == "__main__":
    guardian_brain()
