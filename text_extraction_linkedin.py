from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import random
import csv
from bs4 import BeautifulSoup

# 🔹 CHANGE THIS to your actual Firefox profile path
FIREFOX_PROFILE_PATH = r"C:\Users\lrraw\AppData\Roaming\Mozilla\Firefox\Profiles\AVtzXYQk.Profile 1"

keyword = input("Enter keyword to search on LinkedIn: ").strip()

options = Options()
options.headless = False
options.add_argument("-profile")
options.add_argument(FIREFOX_PROFILE_PATH)

service = Service()
driver = webdriver.Firefox(service=service, options=options)

# =========================
# 1️⃣ Open LinkedIn
# =========================
driver.get("https://www.linkedin.com/feed/")
time.sleep(6)

search_box = driver.find_element(By.XPATH, "//input[contains(@placeholder,'Search')]")
search_box.clear()
search_box.send_keys(keyword)
search_box.send_keys(Keys.ENTER)

time.sleep(random.uniform(4, 6))

# =========================
# 2️⃣ Scroll to load posts
# =========================
for _ in range(10):
    driver.execute_script("window.scrollBy(0, 1000);")
    time.sleep(random.uniform(1, 2))

# =========================
# 3️⃣ REAL-TIME DOM PARSE
# =========================
html = driver.page_source
soup = BeautifulSoup(html, "lxml")

posts = soup.find_all(
    lambda tag: tag.name == "div" and (
        tag.get("data-urn", "").startswith("urn:li:activity")
        or "feed-shared-update-v2" in " ".join(tag.get("class", []))
    )
)

# =========================
# 4️⃣ TEXT-ONLY EXTRACTION
# =========================
extracted_rows = []

for post in posts:

    # ❌ Skip non-text posts
    if post.find("img"):
        continue
    if post.find("video") or post.find(attrs={"data-test-reel-video": True}):
        continue
    if post.find("div", class_="feed-shared-link-preview"):
        continue

    # ✅ Extract text
    text_block = post.find("span", dir="ltr")
    if not text_block:
        continue

    post_text = text_block.get_text(strip=True)
    if len(post_text) < 25:
        continue  # skip noise

    # ✅ Extract author name
    author = "Unknown"
    author_tag = post.find("span", class_="feed-shared-actor__name")
    if author_tag:
        author = author_tag.get_text(strip=True)

    # ✅ Extract post URL (best effort)
    post_url = "N/A"
    for a in post.find_all("a", href=True):
        if "/feed/update/" in a["href"]:
            post_url = a["href"]
            break

    extracted_rows.append([author, post_text, post_url])

# =========================
# 5️⃣ SAVE TO CSV
# =========================
csv_file = "linkedin_text_posts.csv"

with open(csv_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Author Name", "Post Text", "Post URL"])
    writer.writerows(extracted_rows)

# =========================
# 6️⃣ SUMMARY
# =========================
print("\n✅ LINKEDIN TEXT POST EXTRACTION COMPLETE")
print("-" * 45)
print(f"Keyword searched       : {keyword}")
print(f"Total posts scanned    : {len(posts)}")
print(f"Text-only posts saved  : {len(extracted_rows)}")
print(f"CSV file created       : {csv_file}")
print("-" * 45)

time.sleep(5)
driver.quit()
