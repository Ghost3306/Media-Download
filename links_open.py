import webbrowser
import time

LINKS_FILE = "linkedin_post_links.txt"   # change if needed
DELAY_SECONDS = 3          # delay between opening tabs

def open_links_from_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        links = [line.strip() for line in f if line.strip()]

    print(f"Opening {len(links)} links in browser...\n")

    for i, link in enumerate(links, start=1):
        print(f"[{i}/{len(links)}] Opening: {link}")
        webbrowser.open_new_tab(link)
        time.sleep(DELAY_SECONDS)

    print("\n✅ Done opening all links.")

if __name__ == "__main__":
    open_links_from_txt(LINKS_FILE)
