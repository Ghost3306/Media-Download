import yt_dlp
import asyncio
import os
import time
import socket
import ssl
import threading
from concurrent.futures import ThreadPoolExecutor
from curl_cffi import requests as curl_requests

# =========================
# GLOBAL DEBUG COUNTERS
# =========================
active_downloads = 0
completed_downloads = 0
counter_lock = threading.Lock()

def curl_cffi_preflight(url: str) -> bool:
    try:
        session = curl_requests.Session(impersonate="chrome110")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.youtube.com/",
        }

        resp = session.get(url, headers=headers, timeout=20)
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code}")

        return True

    except Exception as e:
        raise RuntimeError(f"CURL_CFFI_PREFLIGHT_FAILED -> {e}")

# =========================
# CONFIG
# =========================
DOWNLOAD_DIR = "downloads"
MAX_WORKERS = 10
BATCH_SIZE = 5
TASK_TIMEOUT = 180
COOLDOWN_BETWEEN_BATCH = 10

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

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
# DOWNLOAD FUNCTION
# =========================
def download_video(url: str):
    global active_downloads, completed_downloads
    thread_name = threading.current_thread().name

    with counter_lock:
        active_downloads += 1
        print(f"[START] {thread_name} | Active: {active_downloads} | URL: {url}")

    try:
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
            "cookiefile": "cookies.txt",
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Referer": "https://www.youtube.com/",
                "Accept-Language": "en-US,en;q=0.9",
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return True, url

    except Exception as e:
        return False, f"{url} -> {classify_exception(e)} -> {e}"

    finally:
        with counter_lock:
            active_downloads -= 1
            completed_downloads += 1
            print(
                f"[DONE ] {thread_name} | Active: {active_downloads} "
                f"| Completed: {completed_downloads}"
            )

# =========================
# MAIN ASYNC RUNNER
# =========================
async def main():
    start_time = time.perf_counter()

    with open("temp.txt", "r") as f:
        links = [l.strip() for l in f if l.strip()]

    total_links = len(links)
    success_links = []
    failed_links = []

    loop = asyncio.get_running_loop()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for i in range(0, total_links, BATCH_SIZE):
            batch = links[i:i + BATCH_SIZE]

            tasks = [
                loop.run_in_executor(executor, download_video, link)
                for link in batch
            ]

            for task in asyncio.as_completed(tasks):
                try:
                    success, info = await asyncio.wait_for(task, timeout=TASK_TIMEOUT)
                    if success:
                        success_links.append(info)
                    else:
                        failed_links.append(info)
                except asyncio.TimeoutError:
                    failed_links.append("TASK_TIMEOUT")

            await asyncio.sleep(COOLDOWN_BETWEEN_BATCH)

    total_time = time.perf_counter() - start_time

    print("\n========== DOWNLOAD SUMMARY ==========")
    print(f"Total links     : {total_links}")
    print(f"Downloaded      : {len(success_links)}")
    print(f"Failed          : {len(failed_links)}")
    print(f"Total time      : {total_time:.2f}s")
    print("=====================================")

# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    asyncio.run(main())
