import yt_dlp
import asyncio
import threading
import time
import os
from concurrent.futures import ThreadPoolExecutor

# =========================
# CONFIG (SAFE VALUES)
# =========================
INPUT_FILE = "temp.txt"
VALID_FILE = "valid_links.txt"
INVALID_FILE = "invalid_links.txt"

COOKIES_FILE = "cookies.txt"

MAX_WORKERS = 3        # VERY IMPORTANT (low)
TASK_TIMEOUT = 60
DELAY_BETWEEN_TASKS = 2  # seconds (anti rate-limit)

# =========================
# SHARED STATE
# =========================
lock = threading.Lock()
valid_links = []
invalid_links = []

# =========================
# COOKIE VALIDATION
# =========================
def verify_cookies_file():
    if not os.path.exists(COOKIES_FILE):
        raise RuntimeError("cookies.txt not found")

    with open(COOKIES_FILE, "r", encoding="utf-8", errors="ignore") as f:
        first_line = f.readline().strip()

    if not first_line.startswith("# Netscape HTTP Cookie File"):
        raise RuntimeError(
            "cookies.txt is NOT Netscape format. Re-export cookies correctly."
        )

# =========================
# LINK CHECK FUNCTION
# =========================
def check_youtube_link(url: str):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "cookiefile": COOKIES_FILE,
        "socket_timeout": 20,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get("title", "Unknown title")
            return True, f"OK | {title}"

    except yt_dlp.utils.DownloadError as e:
        msg = str(e).lower()

        if "confirm you’re not a bot" in msg:
            return None, "Bot check triggered (retry later)"

        if "rate-limited" in msg:
            return None, "Rate limited by YouTube"

        if "private video" in msg:
            return False, "Private video"

        if "sign in to confirm your age" in msg:
            return False, "Age restricted"

        if "video unavailable" in msg:
            return False, "Deleted or unavailable"

        return False, "Invalid or inaccessible"

    except Exception:
        return False, "Invalid URL"

# =========================
# ASYNC WRAPPER
# =========================
async def validate_link(loop, executor, url, index):
    await asyncio.sleep(DELAY_BETWEEN_TASKS)

    try:
        exists, message = await asyncio.wait_for(
            loop.run_in_executor(executor, check_youtube_link, url),
            timeout=TASK_TIMEOUT
        )

        with lock:
            if exists is True:
                valid_links.append(url)
                print(f"{index}. VALID   → {message}")

            elif exists is None:
                # BOT / RATE LIMIT → do NOT mark invalid
                print(f"{index}. SKIPPED → {message}")

            else:
                invalid_links.append(f"{url} | {message}")
                print(f"{index}. INVALID → {message}")

    except asyncio.TimeoutError:
        with lock:
            invalid_links.append(f"{url} | Timeout")
            print(f"{index}. INVALID → Timeout")

# =========================
# MAIN ASYNC RUNNER
# =========================
async def main():
    verify_cookies_file()

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        links = [l.strip() for l in f if l.strip()]

    print(f"Total links found: {len(links)}")
    print("Starting safe async validation...\n")

    loop = asyncio.get_running_loop()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        tasks = [
            validate_link(loop, executor, url, i + 1)
            for i, url in enumerate(links)
        ]

        await asyncio.gather(*tasks)

    if valid_links:
        with open(VALID_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(valid_links))

    if invalid_links:
        with open(INVALID_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(invalid_links))

    print("\nSummary")
    print(f"Valid   : {len(valid_links)}")
    print(f"Invalid : {len(invalid_links)}")
    print("Skipped : Bot / Rate limited (retry later)")

# ========================= 
# ENTRY POINT
# =========================
if __name__ == "__main__":
    asyncio.run(main())
