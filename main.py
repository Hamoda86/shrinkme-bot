import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from twocaptcha import TwoCaptcha

# ✅ رابطك المختصر هنا:
TARGET_URL = "https://shrinkme.ink/KUZP"

VISITS = 100
DELAY_SECONDS = 15
TWO_CAPTCHA_API = "0a88f59668933a935f01996bd1624450"  # ← ضع مفتاحك من 2captcha هنا

def stealth_sync(page):
    page.evaluate("""
        () => {
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Intl.DateTimeFormat = () => ({resolvedOptions: () => ({timeZone: 'America/New_York'})});
        }
    """)
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    page.set_user_agent(ua)
    page.set_viewport_size({"width": 1366, "height": 768})

def solve_recaptcha(solver, site_key, url):
    try:
        print("🧩 حل reCAPTCHA...")
        captcha_id = solver.recaptcha(sitekey=site_key, url=url)
        result = solver.get_result(captcha_id)
        code = result.get('code')
        print("✅ الحل:", code)
        return code
    except Exception as e:
        print("❌ فشل حل الكابتشا:", e)
        return None

def close_popups(page):
    selectors = ["div.popup-close", "button.close", ".modal-close", "div#popup-ad"]
    for sel in selectors:
        try:
            for el in page.query_selector_all(sel):
                el.click()
                print(f"🛑 تم إغلاق: {sel}")
                page.wait_for_timeout(1000)
        except:
            continue

def main():
    solver = TwoCaptcha(TWO_CAPTCHA_API)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for i in range(VISITS):
            print(f"\n🔄 زيارة {i+1}/{VISITS}")
            try:
                context = browser.new_context()
                page = context.new_page()
                stealth_sync(page)

                page.goto(TARGET_URL, timeout=60000)
                page.wait_for_timeout(5000)
                close_popups(page)

                recaptcha_frame = next((f for f in page.frames if "google.com/recaptcha" in f.url), None)
                if recaptcha_frame:
                    site_key = page.eval_on_selector(".g-recaptcha", "el => el.getAttribute('data-sitekey')")
                    if site_key:
                        code = solve_recaptcha(solver, site_key, TARGET_URL)
                        if code:
                            page.evaluate(f'document.getElementById("g-recaptcha-response").innerHTML="{code}";')
                            page.evaluate("""
                                var el = document.getElementById('g-recaptcha-response');
                                if (el) { el.dispatchEvent(new Event('change')); }
                            """)
                            page.wait_for_timeout(5000)

                close_popups(page)

                clicked = False
                for btn in page.query_selector_all("a, button"):
                    try:
                        text = btn.inner_text().lower()
                        if any(k in text for k in ["skip", "get link", "continue", "تخطي", "اذهب", "التالي"]):
                            btn.click()
                            clicked = True
                            print("✅ تم الضغط على الزر")
                            break
                    except:
                        continue

                if not clicked:
                    print("⚠️ لم يتم العثور على زر متابعة")

                page.wait_for_timeout(5000)
                print("✅ الزيارة تمت بنجاح")

            except PlaywrightTimeoutError:
                print("⏱️ انتهت المهلة")
            except Exception as e:
                print(f"❌ خطأ:", e)
            finally:
                try:
                    context.close()
                except:
                    pass
                time.sleep(DELAY_SECONDS)
        browser.close()

if __name__ == "__main__":
    main()

