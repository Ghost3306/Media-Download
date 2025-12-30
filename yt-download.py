import yt_dlp
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"
DOWNLOAD_DIR = "downloads"
MAX_WORKERS = 10

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def download_video(url: str):
    ydl_opts = {
    "format": "worstvideo+bestaudio/best",
    "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
    "noplaylist": True,

    "quiet": True,
    "no_warnings": True,

    "retries": 5,
    "fragment_retries": 5,
    "socket_timeout": 30,

    "http_headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://www.youtube.com/",
        },
    }


    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True, url
    except Exception as e:
        return False, f"{url} -> {e}"


def main():
    start_time = time.perf_counter()

    with open("temp.txt", "r") as f:
        links = [line.strip() for line in f if line.strip()]

    total_links = len(links)
    success_links = []
    failed_links = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(download_video, link) for link in links]

        for future in as_completed(futures):
            success, info = future.result()
            if success:
                success_links.append(info)
            else:
                failed_links.append(info)

    total_time = time.perf_counter() - start_time

    print("\n========== DOWNLOAD SUMMARY ==========")
    print(f"Total links     : {total_links}")
    print(f"Downloaded      : {len(success_links)}")
    print(f"Failed          : {len(failed_links)}")

    if success_links:
        print("\nDownloaded links:")
        for link in success_links:
            print(f"  ✔ {link}")

    if failed_links:
        print("\nFailed links:")
        for link in failed_links:
            print(f"  ✖ {link}")

    print(f"\nTotal time taken: {total_time:.2f} seconds")
    print("=======================================")


if __name__ == "__main__":
    main()
