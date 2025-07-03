from playwright.sync_api import sync_playwright

proxy = "http://37.27.253.44:8014"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, proxy={"server": proxy})
    context = browser.new_context()
    page = context.new_page()

    page.goto("https://api.ipify.org")
    ip = page.inner_text("body")

    print("✅ IP الحالي عبر البروكسي:", ip)

    browser.close()
