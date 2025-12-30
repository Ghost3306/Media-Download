import asyncio
import urllib.parse
from playwright.async_api import async_playwright

async def google_linkedin_posts(keyword, target_links=50):
    query = f'site:linkedin.com/posts "{keyword}"'
    encoded_query = urllib.parse.quote(query)

    results = set()
    page_index = 0   # Google pagination: 0,10,20,...

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,   # IMPORTANT: visible browser
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Linux; Android 11; Pixel 5) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Mobile Safari/537.36"
            ),
            viewport={"width": 412, "height": 915}
        )

        page = await context.new_page()

        while len(results) < target_links and page_index <= 60:
            google_url = (
                f"https://www.google.com/search?"
                f"q={encoded_query}&hl=en&start={page_index}"
            )

            print(f"[INFO] Fetching Google page start={page_index}")
            await page.goto(google_url, timeout=60000)

            # Consent handling
            try:
                await page.click("button:has-text('Accept')", timeout=3000)
            except:
                pass

            await page.wait_for_timeout(4000)

            # Scroll a bit (helps lazy load)
            await page.mouse.wheel(0, 1200)
            await page.wait_for_timeout(2000)

            links = await page.eval_on_selector_all(
                "a[href]",
                "els => els.map(e => e.href)"
            )

            for link in links:
                if "linkedin.com/posts/" in link:
                    clean = link.split("&")[0]
                    results.add(clean)

                    if len(results) >= target_links:
                        break

            page_index += 10   # next Google page
            await page.wait_for_timeout(2500)

        await browser.close()

    return list(results)


async def main():
    keyword = input("Enter keyword: ").strip()
    posts = await google_linkedin_posts(keyword, target_links=50)

    print("\n🔗 LinkedIn Post Links Collected:\n")
    if not posts:
        print("⚠️ No public LinkedIn posts found for this keyword.")
    else:
        for i, p in enumerate(posts, start=1):
            print(f"{i:02d}. {p}")

    print(f"\nTotal links collected: {len(posts)}")

asyncio.run(main())
