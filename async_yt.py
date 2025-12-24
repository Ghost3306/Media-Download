import yt_dlp
import asyncio
import os
import time
import socket
import ssl
from concurrent.futures import ThreadPoolExecutor
from curl_cffi import requests as curl_requests

def curl_cffi_preflight(url: str) -> bool:
    """
    Browser-grade request before yt-dlp touches the URL.
    This reduces 403, throttling, and soft blocks.
    """
    try:
        session = curl_requests.Session(
            impersonate="chrome110"
        )

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
MAX_WORKERS = 10             # safe for YouTube
BATCH_SIZE = 5               # prevents soft-block
TASK_TIMEOUT = 180           # seconds per video
COOLDOWN_BETWEEN_BATCH = 10  # seconds

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
# def download_video(url: str):
#     ydl_opts = {
      
#         "format": "bestvideo[height<=360]+bestaudio/best",
#         "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title).200s_%(id)s.%(ext)s"),
#         "noplaylist": True,

#         "quiet": True,
#         "no_warnings": True,

#         "retries": 2,
#         "fragment_retries": 1,
#         "socket_timeout": 30,
#         "concurrent_fragment_downloads": 8,

#         # 🔐 COOKIES (MOST IMPORTANT)
#         "cookiefile": "cookies.txt",

#         # Browser headers
#         "http_headers": {
#             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
#             "Referer": "https://www.youtube.com/",
#         },
#     }

#     try:
#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             ydl.download([url])
#         return True, url

#     except Exception as e:
#         return False, f"{url} -> {classify_exception(e)} -> {e}"




def download_video(url: str):
    # =========================
    # CURL_CFFI PREFLIGHT
    # =========================
    try:
        curl_cffi_preflight(url)
    except Exception as e:
        return False, f"{url} -> {classify_exception(e)} -> {e}"

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

        # 🔐 COOKIES
        "cookiefile": "cookies.txt",

        # Browser headers (match curl_cffi)
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://www.youtube.com/",
            "Accept-Language": "en-US,en;q=0.9",
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True, url

    except Exception as e:
        return False, f"{url} -> {classify_exception(e)} -> {e}"




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

            # Cool-down to avoid IP throttling
            await asyncio.sleep(COOLDOWN_BETWEEN_BATCH)

    total_time = time.perf_counter() - start_time

    # =========================
    # SUMMARY
    # =========================
    print("\n========== DOWNLOAD SUMMARY ==========")
    print(f"Total links     : {total_links}")
    print(f"Downloaded      : {len(success_links)}")
    print(f"Failed          : {len(failed_links)}")

    if failed_links:
        print("\nFailed links:")
        for f in failed_links:
            print(f"  ✖ {f}")

    print(f"\nTotal time taken: {total_time:.2f} seconds")
    print("=======================================")

# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    asyncio.run(main())
