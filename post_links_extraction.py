from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import random
import csv
from bs4 import BeautifulSoup

# =========================
# CONFIG
# =========================
FIREFOX_PROFILE_PATH = r"C:\Users\lrraw\AppData\Roaming\Mozilla\Firefox\Profiles\AVtzXYQk.Profile 1"
SCROLL_ROUNDS = 10
LINKS_TXT = "linkedin_post_links.txt"
LINKS_CSV = "linkedin_post_links.csv"

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
# POSTS FILTER (IMPORTANT)
# =========================
try:
    posts_btn = driver.find_element(By.XPATH, "//button[contains(.,'Posts')]")
    posts_btn.click()
    time.sleep(5)
except:
    print("⚠️ Posts filter not found — continuing anyway")

# =========================
# SCROLL + COLLECT POST LINKS (URN-BASED)
# =========================
post_links = set()
seen_urns = set()

for round_no in range(SCROLL_ROUNDS):
    print(f"[INFO] Scroll {round_no + 1}/{SCROLL_ROUNDS}")

    driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
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

        # 🔥 RELIABLE LINK CREATION FROM URN
        activity_id = urn.split(":")[-1]
        post_url = f"https://www.linkedin.com/feed/update/urn:li:activity:{activity_id}"

        post_links.add(post_url)

# =========================
# SAVE LINKS (TXT)
# =========================
with open(LINKS_TXT, "w", encoding="utf-8") as f:
    for link in sorted(post_links):
        f.write(link + "\n")

# =========================
# SAVE LINKS (CSV)
# =========================
with open(LINKS_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Post URL"])
    for link in sorted(post_links):
        writer.writerow([link])

# =========================
# SUMMARY
# =========================
print("\n✅ LINKEDIN POST LINK EXTRACTION COMPLETE")
print("-" * 60)
print(f"Keyword searched     : {keyword}")
print(f"Scroll rounds        : {SCROLL_ROUNDS}")
print(f"Unique posts found   : {len(seen_urns)}")
print(f"Post links saved     : {len(post_links)}")
print(f"TXT file             : {LINKS_TXT}")
print(f"CSV file             : {LINKS_CSV}")
print("-" * 60)

time.sleep(5)
driver.quit()
