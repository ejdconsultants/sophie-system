# kill_bot.py
import psutil, time

for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        name = proc.info['name']
        cmdline = proc.info['cmdline'] or []
        if name and name.lower().startswith('python') and 'revenant_bot.py' in ' '.join(cmdline):
            proc.kill()
            print(f"Killed process {proc.pid} (revenant_bot.py)")
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        continue

print("Revenant Bot processes terminated.")
time.sleep(2)
