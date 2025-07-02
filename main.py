import time
import random
import socket
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from twocaptcha import TwoCaptcha

# === إعدادات ===
TARGET_URL = "https://shrinkme.ink/KUZP"
VISITS = 1000
DELAY_SECONDS = 15
TWO_CAPTCHA_API = "0a88f59668933a935f01996bd1624450"

PROXIES = [
    "138.68.60.8:8080",
    "104.248.63.15:30588",
    "165.22.81.6:8080",
    "103.216.82.36:6667",
    "51.158.119.88:8811"
]

# === تفعيل التخفي اليدوي (stealth) ===
def stealth_sync(page):
    page.evaluate("""
        () => {
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
        }
    """)

# === التحقق من أن البروكسي يعمل ===
def is_proxy_alive(proxy):
    try:
        proxy_address = proxy.replace("http://", "")
        host, port = proxy_address.split(":")
        socket.setdefaulttimeout(5)
        socket.create_connection((host, int(port)))
        return True
    except:
        return False

# === حل reCAPTCHA باستخدام 2captcha ===
def solve_recaptcha(solver, site_key, url):
    print("🧩 جاري حل reCAPTCHA ...")
    captcha_id = solver.recaptcha(sitekey=site_key, url=url)
    result = solver.get_result(captcha_id)
    solution = result.get('code')
    print("✅ تم الحل:", solution)
    return solution

# === إغلاق النوافذ المنبثقة ===
def close_popups(page):
    try:
        popup_selectors = [
            "div.popup-close", "button.close",
            ".modal-close", "div#popup-ad",
            "iframe[src*='ads']"
        ]
        for selector in popup_selectors:
            elements = page.query_selector_all(selector)
            for el in elements:
                try:
                    el.click()
                    print(f"🛑 تم إغلاق نافذة: {selector}")
                    page.wait_for_timeout(1000)
                except:
                    continue
    except Exception as e:
        print(f"⚠️ خطأ أثناء إغلاق النوافذ: {e}")

# === الكود الرئيسي ===
def main():
    solver = TwoCaptcha(TWO_CAPTCHA_API)

    with sync_playwright() as p:
        for i in range(VISITS):
            proxy = None
            for attempt in range(len(PROXIES)):
                candidate = "http://" + random.choice(PROXIES).replace("http://", "")
                if is_proxy_alive(candidate):
                    proxy = candidate
                    break

            if not proxy:
                print("❌ لا يوجد أي بروكسي شغال حالياً.")
                return

            print(f"\n🔄 زيارة {i+1}/{VISITS} باستخدام البروكسي: {proxy}")

            try:
                browser = p.chromium.launch(headless=True, proxy={"server": proxy})
                context = browser.new_context()
                page = context.new_page()
                stealth_sync(page)

                page.goto(TARGET_URL, timeout=60000)
                page.wait_for_timeout(5000)

                close_popups(page)

                # التحقق من وجود reCAPTCHA
                recaptcha_frame = next((f for f in page.frames if "google.com/recaptcha" in f.url), None)

                if recaptcha_frame:
                    site_key = None
                    try:
                        site_key = recaptcha_frame.eval_on_selector(
                            ".g-recaptcha", "el => el.getAttribute('data-sitekey')"
                        )
                    except:
                        pass

                    if not site_key:
                        try:
                            site_key = page.eval_on_selector(
                                ".g-recaptcha", "el => el.getAttribute('data-sitekey')"
                            )
                        except:
                            pass

                    if site_key:
                        solution = solve_recaptcha(solver, site_key, TARGET_URL)
                        page.evaluate(
                            f'document.getElementById("g-recaptcha-response").innerHTML="{solution}";'
                        )
                        page.evaluate("""
                            var el = document.getElementById('g-recaptcha-response');
                            if (el) { el.dispatchEvent(new Event('change')); }
                        """)
                        page.wait_for_timeout(5000)
                    else:
                        print("⚠️ لم يتم العثور على sitekey")

                close_popups(page)

                # الضغط على زر "تخطي" أو "استمرار"
                clicked = False
                buttons = page.query_selector_all("a, button")
                for btn in buttons:
                    try:
                        text = btn.inner_text().lower()
                        if any(k in text for k in ["skip", "get link", "continue"]):
                            btn.click()
                            print("✅ تم الضغط على زر المتابعة")
                            clicked = True
                            break
                    except:
                        continue

                if not clicked:
                    print("⚠️ لم يتم العثور على زر المتابعة")

                page.wait_for_timeout(5000)
                print("✅ الزيارة مكتملة")

            except PlaywrightTimeoutError:
                print("❌ انتهاء المهلة")
            except Exception as e:
                print(f"❌ خطأ أثناء الزيارة: {e}")
            finally:
                browser.close()
                print(f"⏳ الانتظار {DELAY_SECONDS} ثانية ...")
                time.sleep(DELAY_SECONDS)

if __name__ == "__main__":
    main()

