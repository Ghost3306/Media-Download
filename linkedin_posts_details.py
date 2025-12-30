from selenium import webdriver 
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import random
from bs4 import BeautifulSoup

FIREFOX_PROFILE_PATH = r"C:\Users\lrraw\AppData\Roaming\Mozilla\Firefox\Profiles\AVtzXYQk.Profile 1"

keyword = input("Enter keyword to search on LinkedIn: ").strip()

options = Options()
options.headless = False
options.add_argument("-profile")
options.add_argument(FIREFOX_PROFILE_PATH)

service = Service()
driver = webdriver.Firefox(service=service, options=options)

# 🔹 Open LinkedIn feed
driver.get("https://www.linkedin.com/feed/")
time.sleep(6)

# 🔹 Search keyword
search_box = driver.find_element(By.XPATH, "//input[contains(@placeholder,'Search')]")
search_box.clear()
search_box.send_keys(keyword)
search_box.send_keys(Keys.ENTER)

# 🔹 Allow results to load
time.sleep(random.uniform(4, 6))

# 🔹 Scroll to load posts
for _ in range(5):
    driver.execute_script("window.scrollBy(0, 900);")
    time.sleep(random.uniform(1, 2))

# =====================================================
# 🔥 REAL-TIME DOM ANALYSIS STARTS HERE
# =====================================================
html = driver.page_source
soup = BeautifulSoup(html, "lxml")

# 🔹 Broad post container detection
posts = soup.find_all(
    lambda tag: tag.name == "div" and (
        tag.get("data-urn", "").startswith("urn:li:activity")
        or "feed-shared-update-v2" in " ".join(tag.get("class", []))
    )
)

text_only = 0
text_with_link = 0
image_posts = 0
video_posts = 0
unknown_posts = 0

for post in posts:
    has_text = False
    has_image = False
    has_video = False
    has_link = False

    # 🔹 TEXT (multiple patterns)
    if (
        post.find("span", attrs={"dir": "ltr"})
        or post.find("div", class_="feed-shared-text")
        or post.find("div", class_="update-components-text")
    ):
        has_text = True

    # 🔹 VIDEO (strong signals)
    if (
        post.find("video")
        or post.find(attrs={"data-test-reel-video": True})
        or post.find("div", class_="feed-shared-video")
    ):
        has_video = True

    # 🔹 IMAGE / CAROUSEL
    if (
        post.find("img")
        or post.find("div", class_="feed-shared-image")
        or post.find("div", class_="feed-shared-carousel")
    ):
        has_image = True

    # 🔹 LINK PREVIEW
    if (
        post.find("a", href=True)
        and post.find("div", class_="feed-shared-link-preview")
    ):
        has_link = True

    # 🔹 Classification priority
    if has_video:
        video_posts += 1
    elif has_image:
        image_posts += 1
    elif has_text and has_link:
        text_with_link += 1
    elif has_text:
        text_only += 1
    else:
        unknown_posts += 1

# 🔹 Results
print("\n📊 LINKEDIN POST ANALYSIS (ROBUST)")
print("-" * 45)
print(f"Total post containers : {len(posts)}")
print(f"📝 Text-only posts     : {text_only}")
print(f"🔗 Text + link posts   : {text_with_link}")
print(f"🖼️ Image posts         : {image_posts}")
print(f"🎥 Video posts         : {video_posts}")
print(f"❓ Unknown posts       : {unknown_posts}")
print("-" * 45)
