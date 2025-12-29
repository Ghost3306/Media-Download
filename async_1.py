import yt_dlp
import asyncio
import os
import time
import socket
import ssl
import threading
import sys
import contextlib
import io
from concurrent.futures import ThreadPoolExecutor
from curl_cffi import requests as curl_requests
import traceback
# =========================
# CONFIG
# =========================
DOWNLOAD_DIR = "downloads"
COOKIES_FILE = "cookies.txt"
INPUT_FILE = "yt-links.txt"
SKIPPED_FILE = "skipped_links.txt"

MAX_WORKERS = 8
BATCH_SIZE = 5
TASK_TIMEOUT = 180
COOLDOWN_BETWEEN_BATCH = 10

MAX_RETRY_ROUNDS = 3
RETRY_COOLDOWN = 180  # 3 minutes

# =========================
# GLOBAL COUNTERS
# =========================
active_downloads = 0
completed_downloads = 0
failed_downloads = 0
skipped_downloads = 0
total_links_global = 0

skipped_links = []

counter_lock = threading.Lock()
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# =========================
# CURL_CFFI PREFLIGHT
# =========================
def curl_cffi_preflight(url: str) -> bool:
    session = curl_requests.Session(impersonate="chrome110")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.youtube.com/",
    }
    resp = session.get(url, headers=headers, timeout=20)
    if resp.status_code != 200:
        raise RuntimeError("PREFLIGHT_FAILED")
    return True

# =========================
# STATUS LINE
# =========================
def print_status_line():
    remaining = (
        total_links_global
        - completed_downloads
        - failed_downloads
        - skipped_downloads
    )
    sys.stdout.write(
        f"\rRemaining: {remaining} | "
        f"Downloaded: {completed_downloads} | "
        f"Failed: {failed_downloads} | "
        f"Skipped: {skipped_downloads} | "
        f"Active: {active_downloads}   "
    )
    sys.stdout.flush()

# =========================
# DOWNLOAD FUNCTION
# =========================
def download_video(url: str):
    global active_downloads, completed_downloads, failed_downloads, skipped_downloads

    with counter_lock:
        active_downloads += 1
        print_status_line()

    video_title = None

    try:
        # ---- METADATA CHECK ----
        with contextlib.redirect_stderr(io.StringIO()):
            with yt_dlp.YoutubeDL({
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "cookiefile": COOKIES_FILE,
            }) as ydl:
                info = ydl.extract_info(url, download=False)
                video_title = info.get("title")

        if not video_title:
            raise RuntimeError("BOT_CHECK")

        print(f"\nStarted | {video_title}")

        curl_cffi_preflight(url)

        ydl_opts = {
            "format": "bestvideo[height<=360]+bestaudio/best",
            "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title).200s_%(id)s.%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "retries": 2,
            "fragment_retries": 1,
            "socket_timeout": 30,
            "concurrent_fragment_downloads": 8,
            "cookiefile": COOKIES_FILE,
        }

        with contextlib.redirect_stderr(io.StringIO()):
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        with counter_lock:
            completed_downloads += 1

    except Exception as e:
        
        with counter_lock:
            skipped_downloads += 1
            skipped_links.append(url)
        print("[ERROR] Raw exception:", repr(e))
    finally:
        with counter_lock:
            active_downloads -= 1
            print_status_line()
            if video_title:
                print(f"\nFinished | {video_title}")
            else:
                print("\nSkipped | Bot / Rate limit")

# =========================
# RUN BATCHES
# =========================
async def run_batches(links, workers):
    loop = asyncio.get_running_loop()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        for i in range(0, len(links), BATCH_SIZE):
            batch = links[i:i + BATCH_SIZE]

            tasks = [
                loop.run_in_executor(executor, download_video, link)
                for link in batch
            ]

            for task in asyncio.as_completed(tasks):
                try:
                    await asyncio.wait_for(task, timeout=TASK_TIMEOUT)
                except asyncio.TimeoutError:
                    pass

            await asyncio.sleep(COOLDOWN_BETWEEN_BATCH)

# =========================
# MAIN
# =========================
async def main():
    global total_links_global

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        links = [l.strip() for l in f if l.strip()]

    total_links_global = len(links)

    print(f"Total links: {total_links_global}")
    print("----------------------------------")

    # ---------- INITIAL RUN ----------
    await run_batches(links, MAX_WORKERS)

    # ---------- RETRY LOGIC ----------
    retry_round = 1

    while skipped_links and retry_round <= MAX_RETRY_ROUNDS:
        with open(SKIPPED_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(skipped_links))

        retry_links = skipped_links.copy()
        skipped_links.clear()

        workers = max(2, MAX_WORKERS - retry_round * 2)

        print(
            f"\nRetry round {retry_round} | "
            f"Links: {len(retry_links)} | "
            f"Workers: {workers}"
        )

        print(f"Cooling down for {RETRY_COOLDOWN // 60} minutes...")
        time.sleep(RETRY_COOLDOWN)

        await run_batches(retry_links, workers)
        retry_round += 1

    # ---------- FINAL SUMMARY ----------
    print("\n\nFinal Summary")
    print(f"Total       : {total_links_global}")
    print(f"Downloaded  : {completed_downloads}")
    print(f"Failed      : {failed_downloads}")
    print(f"Skipped     : {skipped_downloads}")

    if skipped_links:
        with open(SKIPPED_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(skipped_links))
        print(f"Remaining skipped saved to {SKIPPED_FILE}")

# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    asyncio.run(main())
