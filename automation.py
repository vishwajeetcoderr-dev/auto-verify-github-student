import asyncio, random, os, requests, base64
from datetime import datetime
from playwright.async_api import async_playwright
from config import HEADLESS, MIN_DELAY, MAX_DELAY, TIMEOUT, SCREENSHOTS_DIR, log

# ─── CAMPUS GPS COORDS ──────────────────────────
CAMPUS_COORDS = {
    "Universitas Indonesia":               (-6.3614,  106.8305),
    "Institut Teknologi Bandung":          (-6.8944,  107.6106),
    "Universitas Gadjah Mada":            (-7.7714,  110.3773),
    "Institut Teknologi Sepuluh Nopember": (-7.2756,  112.7965),
    "Universitas Airlangga":              (-7.2679,  112.7624),
    "Universitas Brawijaya":              (-7.9513,  112.6145),
    "Universitas Diponegoro":             (-7.0524,  110.4380),
    "Universitas Bina Nusantara":         (-6.2021,  106.7842),
    "Universitas Padjadjaran":            (-6.9175,  107.6191),
    "Universitas Pelita Harapan":         (-6.2397,  106.6513),
}

# ─── HELPERS ────────────────────────────────────
async def human_delay(min_s=None, max_s=None):
    await asyncio.sleep(random.uniform(
        min_s or MIN_DELAY,
        max_s or MAX_DELAY
    ))

async def apply_stealth(page):
    scripts = [
        "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})",
        "Object.defineProperty(navigator,'language',{get:()=>'id-ID'})",
        "Object.defineProperty(navigator,'languages',{get:()=>['id-ID','id','en']})",
        "Object.defineProperty(navigator,'plugins',{get:()=>[1,2,3,4,5]})",
    ]
    for s in scripts:
        await page.evaluate(s)

# ─── COOKIE HANDLER ─────────────────────────────
def parse_cookies(cookie_str):
    cookies = []
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            name, value = part.split("=", 1)
            cookies.append({
                "name":   name.strip(),
                "value":  value.strip(),
                "domain": ".github.com",
                "path":   "/"
            })
    return cookies

async def inject_cookies(context, cookie_str):
    cookies = parse_cookies(cookie_str)
    await context.add_cookies(cookies)

def verify_cookie(cookie_str):
    try:
        resp = requests.get(
            "https://api.github.com/user",
            headers={"Cookie": cookie_str},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            return True, {
                "username":    data.get("login"),
                "name":        data.get("name", "N/A"),
                "email":       data.get("email", "N/A"),
                "followers":   data.get("followers", 0),
                "repos":       data.get("public_repos", 0),
                "created":     data.get("created_at", "")[:10],
                "account_age": (datetime.now() - datetime.fromisoformat(
                    data.get("created_at","2020-01-01T00:00:00Z").replace("Z","+00:00")
                )).days
            }
        return False, {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return False, {"error": str(e)}

def set_profile(cookie_str, name, uni, city):
    try:
        requests.patch(
            "https://api.github.com/user",
            headers={"Cookie": cookie_str, "Content-Type": "application/json"},
            json={
                "name":     name,
                "location": f"{city}, Indonesia",
                "bio":      f"Student at {uni}"
            },
            timeout=10
        )
        log.info("✅ GitHub profile updated")
    except Exception as e:
        log.warning(f"Profile update failed: {e}")

# ─── BROWSER AUTOMATION ─────────────────────────
class Automation:
    def __init__(self, cookie, school, name, uni_name):
        self.cookie   = cookie
        self.school   = school
        self.name     = name
        self.uni_name = uni_name
        self.page     = None
        self.context  = None
        self.browser  = None

    async def run(self, doc_paths):
        async with async_playwright() as p:
            coords = CAMPUS_COORDS.get(self.uni_name, (-6.2088, 106.8456))

            self.browser = await p.chromium.launch(
                headless=HEADLESS,
                args=[
                    "--use-fake-device-for-media-stream",
                    f"--use-file-for-fake-video-capture={doc_paths['student_id']}",
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ]
            )
            self.context = await self.browser.new_context(
                locale="id-ID",
                timezone_id="Asia/Jakarta",
                geolocation={"latitude": coords[0], "longitude": coords[1]},
                permissions=["geolocation"],
                user_agent="Mozilla/5.0 (Linux; Android 13; Redmi Note 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
                viewport={"width": 390, "height": 844},
                extra_http_headers={"Accept-Language": "id-ID,id;q=0.9"}
            )

            # Inject cookies
            await inject_cookies(self.context, self.cookie)
            self.page = await self.context.new_page()
            await apply_stealth(self.page)

            try:
                result = await self._run_flow(doc_paths)
                return result
            finally:
                await self.browser.close()

    async def _run_flow(self, doc_paths):
        # Step 1 — Navigate
        log.info("GHS 1/5: Navigating...")
        await self.page.goto(
            "https://education.github.com/discount_requests/new",
            timeout=TIMEOUT, wait_until="networkidle"
        )
        await human_delay(2, 3)

        # Step 2 — Click start
        log.info("GHS 2/5: Clicking apply button...")
        for sel in ["button:has-text('Start')", "a:has-text('Start')",
                    "button:has-text('Apply')", "button.primary"]:
            try:
                el = await self.page.query_selector(sel)
                if el:
                    await el.click()
                    await human_delay(1, 2)
                    break
            except:
                continue

        # Step 3 — Fill form
        log.info("GHS 3/5: Filling form...")
        for sel in ["input[placeholder*='school']", "input[placeholder*='School']",
                    "input[name='school']", "input[type='text']"]:
            try:
                el = await self.page.query_selector(sel)
                if el and await el.is_visible():
                    await el.fill(self.school)
                    await human_delay(1, 2)
                    break
            except:
                continue

        # Step 4 — Upload docs (enrollment letter first)
        log.info("GHS 4/5: Uploading documents...")
        upload_order = [
            doc_paths.get("enrollment_letter"),
            doc_paths.get("student_id"),
            doc_paths.get("transcript")
        ]
        file_inputs = await self.page.query_selector_all("input[type=file]")
        uploaded = 0
        for file_input, doc_path in zip(file_inputs, upload_order):
            if doc_path and os.path.exists(doc_path):
                await file_input.set_input_files(doc_path)
                await human_delay(1, 2)
                uploaded += 1
        log.info(f"GHS ✅ {uploaded} docs uploaded")

        # Step 5 — Submit
        log.info("GHS 5/5: Submitting...")
        for sel in ["button:has-text('Submit')", "button[type=submit]",
                    "button:has-text('Complete')", "button.primary"]:
            try:
                el = await self.page.query_selector(sel)
                if el and await el.is_visible():
                    await el.click()
                    await human_delay(2, 3)
                    break
            except:
                continue

        # Screenshot
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"{SCREENSHOTS_DIR}/submit_{ts}.png"
        await self.page.screenshot(path=path, full_page=True)
        log.info(f"GHS ✅ Screenshot: {path}")
        return {"screenshot": path, "status": "PENDING"}

# ─── STATUS CHECKER ─────────────────────────────
def check_approval(cookie_str):
    try:
        resp = requests.get(
            "https://education.github.com/api/student_status",
            headers={"Cookie": cookie_str},
            timeout=10
        )
        text = str(resp.text).lower()
        if any(x in text for x in ["approved","active","benefits_active"]):
            return "APPROVED"
        elif any(x in text for x in ["denied","rejected"]):
            return "REJECTED"
        return "PENDING"
    except:
        return "PENDING"
