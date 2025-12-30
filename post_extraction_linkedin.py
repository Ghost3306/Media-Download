# from selenium import webdriver
# from selenium.webdriver.firefox.service import Service
# from selenium.webdriver.firefox.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# import time
# import random
# import csv
# import os
# import requests
# from urllib.parse import urlparse
# from bs4 import BeautifulSoup

# # =========================
# # CONFIG
# # =========================
# FIREFOX_PROFILE_PATH = r"C:\Users\lrraw\AppData\Roaming\Mozilla\Firefox\Profiles\AVtzXYQk.Profile 1"
# IMAGE_DIR = "downloads/images"
# CSV_FILE = "linkedin_text_posts.csv"
# SCROLL_ROUNDS = 10

# os.makedirs(IMAGE_DIR, exist_ok=True)

# keyword = input("Enter keyword to search on LinkedIn: ").strip()

# # =========================
# # SELENIUM SETUP
# # =========================
# options = Options()
# options.headless = False
# options.add_argument("-profile")
# options.add_argument(FIREFOX_PROFILE_PATH)

# service = Service()
# driver = webdriver.Firefox(service=service, options=options)

# # =========================
# # OPEN LINKEDIN
# # =========================
# driver.get("https://www.linkedin.com/feed/")
# time.sleep(6)

# search_box = driver.find_element(By.XPATH, "//input[contains(@placeholder,'Search')]")
# search_box.clear()
# search_box.send_keys(keyword)
# search_box.send_keys(Keys.ENTER)

# time.sleep(random.uniform(4, 6))

# # =========================
# # IMAGE DOWNLOAD HELPER
# # =========================
# def download_image(url, filename):
#     try:
#         headers = {
#             "User-Agent": "Mozilla/5.0",
#             "Referer": "https://www.linkedin.com/"
#         }
#         r = requests.get(url, headers=headers, timeout=15)
#         if r.status_code == 200:
#             with open(filename, "wb") as f:
#                 f.write(r.content)
#             return True
#     except Exception as e:
#         print(f"    [!] Image download failed: {e}")
#     return False

# # =========================
# # REAL-TIME SCROLL + EXTRACT
# # =========================
# seen_urns = set()
# extracted_rows = []

# for round_no in range(SCROLL_ROUNDS):
#     print(f"[INFO] Scroll round {round_no + 1}/{SCROLL_ROUNDS}")

#     driver.execute_script("window.scrollBy(0, 1000);")
#     time.sleep(random.uniform(1.5, 2.5))

#     soup = BeautifulSoup(driver.page_source, "lxml")

#     posts = soup.find_all(
#         lambda tag: tag.name == "div" and (
#             tag.get("data-urn", "").startswith("urn:li:activity")
#             or "feed-shared-update-v2" in " ".join(tag.get("class", []))
#         )
#     )

#     for post in posts:
#         urn = post.get("data-urn")
#         if not urn or urn in seen_urns:
#             continue

#         seen_urns.add(urn)

#         # =========================
#         # IMAGE HANDLING (SKIP PROFILE PHOTOS)
#         # =========================
#         content_images = []

#         for img in post.find_all("img"):
#             img_url = img.get("data-delayed-url") or img.get("src")
#             if not img_url or img_url.startswith("data:image"):
#                 continue

#             img_class = " ".join(img.get("class", []))

#             # ❌ Skip profile / avatar / logo images
#             if any(x in img_class.lower() for x in [
#                 "avatar", "entityphoto", "profile", "ghost", "logo"
#             ]):
#                 continue

#             # ❌ Skip very small icons
#             if img.get("width") and int(img.get("width", 0)) < 100:
#                 continue

#             content_images.append(img_url)

#         # Download content images
#         for idx, img_url in enumerate(content_images, start=1):
#             ext = os.path.splitext(urlparse(img_url).path)[1] or ".jpg"
#             filename = f"{IMAGE_DIR}/{urn.replace(':', '_')}_{idx}{ext}"

#             if download_image(img_url, filename):
#                 print(f"  🖼️ Image saved: {filename}")



# # =========================
# # 3️⃣ REAL-TIME DOM PARSE
# # =========================
# html = driver.page_source
# soup = BeautifulSoup(html, "lxml")

# posts = soup.find_all(
#     lambda tag: tag.name == "div" and (
#         tag.get("data-urn", "").startswith("urn:li:activity")
#         or "feed-shared-update-v2" in " ".join(tag.get("class", []))
#     )
# )

# # =========================
# # 4️⃣ TEXT-ONLY EXTRACTION
# # =========================
# extracted_rows = []

# for post in posts:

#     # ❌ Skip non-text posts
#     if post.find("img"):
#         continue
#     if post.find("video") or post.find(attrs={"data-test-reel-video": True}):
#         continue
#     if post.find("div", class_="feed-shared-link-preview"):
#         continue

#     # ✅ Extract text
#     text_block = post.find("span", dir="ltr")
#     if not text_block:
#         continue

#     post_text = text_block.get_text(strip=True)
#     if len(post_text) < 25:
#         continue  # skip noise

#     # ✅ Extract author name
#     author = "Unknown"
#     author_tag = post.find("span", class_="feed-shared-actor__name")
#     if author_tag:
#         author = author_tag.get_text(strip=True)

#     # ✅ Extract post URL (best effort)
#     post_url = "N/A"
#     for a in post.find_all("a", href=True):
#         if "/feed/update/" in a["href"]:
#             post_url = a["href"]
#             break

#     extracted_rows.append([author, post_text, post_url])

# # =========================
# # 5️⃣ SAVE TO CSV
# # =========================
# csv_file = "linkedin_text_posts.csv"

# with open(csv_file, "w", newline="", encoding="utf-8") as f:
#     writer = csv.writer(f)
#     writer.writerow(["Author Name", "Post Text", "Post URL"])
#     writer.writerows(extracted_rows)


# # =========================
# # SUMMARY
# # =========================
# print("\n✅ LINKEDIN REAL-TIME EXTRACTION COMPLETE")
# print("-" * 60)
# print(f"Keyword searched        : {keyword}")
# print(f"Unique posts scanned    : {len(seen_urns)}")
# print(f"Text-only posts saved   : {len(extracted_rows)}")
# print(f"Images saved in folder  : {IMAGE_DIR}")
# print(f"CSV file created        : {CSV_FILE}")
# print("-" * 60)

# time.sleep(5)
# driver.quit()

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import random
import csv
import os
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# =========================
# CONFIG
# =========================
FIREFOX_PROFILE_PATH = r"C:\Users\lrraw\AppData\Roaming\Mozilla\Firefox\Profiles\AVtzXYQk.Profile 1"
IMAGE_DIR = "downloads/images"
CSV_FILE = "linkedin_text_posts.csv"
SCROLL_ROUNDS = 10

os.makedirs(IMAGE_DIR, exist_ok=True)

keyword = input("Enter keyword to search on LinkedIn: ").strip()

# =========================
# SELENIUM SETUP
# =========================
options = Options()
options.headless = False
options.add_argument("-profile")
options.add_argument(FIREFOX_PROFILE_PATH)

service = Service()
driver = webdriver.Firefox(service=service, options=options)

# =========================
# OPEN LINKEDIN
# =========================
driver.get("https://www.linkedin.com/feed/")
time.sleep(6)

search_box = driver.find_element(By.XPATH, "//input[contains(@placeholder,'Search')]")
search_box.clear()
search_box.send_keys(keyword)
search_box.send_keys(Keys.ENTER)

time.sleep(random.uniform(5, 7))

# =========================
# 🔹 POSTS FILTER (PROPER SORTING)
# =========================
try:
    posts_btn = driver.find_element(By.XPATH, "//button[contains(.,'Posts')]")
    posts_btn.click()
    time.sleep(5)
except:
    print("⚠️ Posts filter not found — continuing anyway")

# =========================
# IMAGE DOWNLOAD HELPER
# =========================
def download_image(url, filename):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.linkedin.com/"
        }
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            with open(filename, "wb") as f:
                f.write(r.content)
            return True
    except Exception as e:
        print(f"    [!] Image download failed: {e}")
    return False

# =========================
# REAL-TIME SCROLL + IMAGE EXTRACT
# =========================
seen_urns = set()

for round_no in range(SCROLL_ROUNDS):
    print(f"[INFO] Scroll round {round_no + 1}/{SCROLL_ROUNDS}")

    driver.execute_script("window.scrollBy(0, 1200);")
    time.sleep(random.uniform(2.5, 3.5))

    soup = BeautifulSoup(driver.page_source, "lxml")

    posts = soup.find_all(
        lambda tag: tag.name == "div" and (
            tag.get("data-urn", "").startswith("urn:li:activity")
            or "feed-shared-update-v2" in " ".join(tag.get("class", []))
        )
    )

    for post in posts:
        urn = post.get("data-urn")
        if not urn or urn in seen_urns:
            continue

        seen_urns.add(urn)

        content_images = []

        for img in post.find_all("img"):
            img_url = img.get("data-delayed-url") or img.get("src")
            if not img_url or img_url.startswith("data:image"):
                continue

            img_class = " ".join(img.get("class", []))

            if any(x in img_class.lower() for x in [
                "avatar", "entityphoto", "profile", "ghost", "logo"
            ]):
                continue

            if img.get("width") and int(img.get("width", 0)) < 100:
                continue

            content_images.append(img_url)

        for idx, img_url in enumerate(content_images, start=1):
            ext = os.path.splitext(urlparse(img_url).path)[1] or ".jpg"
            filename = f"{IMAGE_DIR}/{urn.replace(':', '_')}_{idx}{ext}"

            if download_image(img_url, filename):
                print(f"  🖼️ Image saved: {filename}")

# =========================
# TEXT-ONLY EXTRACTION
# =========================
html = driver.page_source
soup = BeautifulSoup(html, "lxml")

posts = soup.find_all(
    lambda tag: tag.name == "div" and (
        tag.get("data-urn", "").startswith("urn:li:activity")
        or "feed-shared-update-v2" in " ".join(tag.get("class", []))
    )
)

extracted_rows = []

for post in posts:
    if post.find("img"):
        continue
    if post.find("video") or post.find(attrs={"data-test-reel-video": True}):
        continue
    if post.find("div", class_="feed-shared-link-preview"):
        continue

    text_block = post.find("span", dir="ltr")
    if not text_block:
        continue

    post_text = text_block.get_text(strip=True)
    if len(post_text) < 25:
        continue

    author = "Unknown"
    author_tag = post.find("span", class_="feed-shared-actor__name")
    if author_tag:
        author = author_tag.get_text(strip=True)

    post_url = "N/A"
    for a in post.find_all("a", href=True):
        if "/feed/update/" in a["href"]:
            post_url = a["href"].split("?")[0]
            break

    extracted_rows.append([author, post_text, post_url])

# =========================
# SAVE CSV
# =========================
with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Author Name", "Post Text", "Post URL"])
    writer.writerows(extracted_rows)

# =========================
# SUMMARY
# =========================
print("\n✅ LINKEDIN REAL-TIME EXTRACTION COMPLETE")
print("-" * 60)
print(f"Keyword searched        : {keyword}")
print(f"Unique posts scanned    : {len(seen_urns)}")
print(f"Text-only posts saved   : {len(extracted_rows)}")
print(f"Images saved in folder  : {IMAGE_DIR}")
print(f"CSV file created        : {CSV_FILE}")
print("-" * 60)

time.sleep(5)
driver.quit()
