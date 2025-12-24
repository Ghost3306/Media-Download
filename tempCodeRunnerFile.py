import yt_dlp
import asyncio
import os
import time
import socket
import ssl
import threading
from concurrent.futures import ThreadPoolExecutoar
from curl_cffi import requests as curl_requests

# =========================
# CONFIG
# =========================
DOWNLOAD_DIR = "downloads"
MAX_WORKERS = 3
BATCH_SIZE = 5
TASK_TIMEOUT = 180
COOLDOWN_BETWEEN_BATCH = 10
COOKIE_FILE = "cookies.txt"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# =========================
# GLOBAL PROGRESS STATE
# =========================
progress_lock = threading.Lock()
TOTAL_TASKS = 0
COMPLETED_TASKS = 0
ACTIVE_TASKS = 0

# =========================
# ERROR CLASSIFIER
# =========================
def classify_exception(e: Exception) -> str:
    msg = str(e).lower()
    if "403" in msg:
        return "403_FORBIDDEN"
    if "winerror 10054" in msg:
        return "CONNECTION_RESET"
    if "timed out" in msg:
        return "TIMEOUT"
    if isinstance(e, ssl.SSLError):
        return "SSL_ERROR"
    if isinstance(e, socket.timeout):
        return "SOCKET_TIMEOUT"
    return "UNKNOWN_ERROR"

# =========================
# GLOBAL PROGRESS PRINTER
# =========================
def print_global_progress():
    with progress_lock:
        print(
            f"\r[Workers: {ACTIVE_TASKS}/{MAX_WORKERS}] "
            f"[Completed: {COMPLETED_TASKS}/{TOTAL_TASKS}] "
            f"[Active: {ACTIVE_TASKS}]",
            end="",
            flush=True,
        )

# =========================
# YT-DLP PROGRESS HOOK
# =========================
def ytdlp_progress_hook(d):
    if d.get("status") == "downloading":
        print_global_progress()

# =========================
# CURL_CFFI PREFLIGHT (SAFE & NON-BLOCKING)
# =========================
def curl_cffi_preflight_safe(url: str):
    try:
        session = curl_requests.Session(impersonate="chrome110")
        session.head(url, timeout=3)  # HARD LIMIT
    except Exception:
        pass  # NEVER block yt-dlp

# =========================
# DOWNLOAD FUNCTION
# =========================
def download_video(url: str):
    global ACTIVE_TASKS, COMPLETED_TASKS

    with progress_lock:
        ACTIVE_TASKS += 1
        print_global_progress()

    try:
        # Fire-and-forget curl warmup
        curl_cffi_preflight_safe(url)

        ydl_opts = {
            "format": "bestvideo[height<=360]+bestaudio/best",
            "outtmpl": os.path.join(
                DOWNLOAD_DIR, "%(title).200s_%(id)s.%(ext)s"
            ),
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "retries": 2,
            "fragment_retries": 1,
            "socket_timeout": 30,
            "concurrent_fragment_downloads": 8,
            "cookiefile": COOKIE_FILE,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Referer": "https://www.youtube.com/",
                "Accept-Language": "en-US,en;q=0.9",
            },
            "progress_hooks": [ytdlp_progress_hook],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return True, url

    except Exception as e:
        return False, f"{url} -> {classify_exception(e)} -> {e}"

    finally:
        with progress_lock:
            ACTIVE_TASKS -= 1
            COMPLETED_TASKS += 1
            print_global_progress()

# =========================
# MAIN ASYNC RUNNER
# =========================
async def main():
    global TOTAL_TASKS

    start_time = time.perf_counter()

    with open("temp.txt", "r") as f:
        links = [l.strip() for l in f if l.strip()]

    TOTAL_TASKS = len(links)

    success_links = []
    failed_links = []

    loop = asyncio.get_running_loop()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for i in range(0, TOTAL_TASKS, BATCH_SIZE):
            batch = links[i:i + BATCH_SIZE]

            tasks = [
                loop.run_in_executor(executor, download_video, link)
                for link in batch
            ]

            for task in asyncio.as_completed(tasks):
                try:
                    success, info = await asyncio.wait_for(
                        task, timeout=TASK_TIMEOUT
                    )
                    if success:
                        success_links.append(info)
                    else:
                        failed_links.append(info)
                except asyncio.TimeoutError:
                    failed_links.append("TASK_TIMEOUT")

            await asyncio.sleep(COOLDOWN_BETWEEN_BATCH)

    total_time = time.perf_counter() - start_time

    print("\n\n========== DOWNLOAD SUMMARY ==========")
    print(f"Total links     : {TOTAL_TASKS}")
    print(f"Downloaded      : {len(success_links)}")
    print(f"Failed          : {len(failed_links)}")
    print(f"Total time taken: {total_time:.2f} seconds")
    print("======================================")

# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    asyncio.run(main())
