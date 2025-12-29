import os
import shutil
import time
import random

YTDLP_CACHE = os.path.expanduser("~/.cache/yt-dlp")

def reset_yt_dlp_session():
    print("Resetting yt-dlp session (invisible)...")

    # 1. Remove yt-dlp cache
    if os.path.exists(YTDLP_CACHE):
        shutil.rmtree(YTDLP_CACHE, ignore_errors=True)
        print("yt-dlp cache cleared")

    # 2. Cooldown (VERY IMPORTANT)
    cooldown = random.randint(30, 90)
    print(f"Cooling down for {cooldown} seconds")
    time.sleep(cooldown)

    print("Session reset completed")

if __name__ == "__main__":
    reset_yt_dlp_session()
