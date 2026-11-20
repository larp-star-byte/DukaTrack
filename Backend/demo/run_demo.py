"""Records the demo: python Backend/demo/run_demo.py (server must be running on port 5000)
Makes demo/dukatrack-demo.webm and screenshots in demo/shots/"""
import os, time, shutil
from playwright.sync_api import sync_playwright

URL = "http://localhost:5000"
HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "shots"); os.makedirs(SHOTS, exist_ok=True)
CAPTION_JS = """(t)=>{let d=document.getElementById('demo-cap');if(!d){d=document.createElement('div');d.id='demo-cap';
d.style.cssText='position:fixed;top:0;left:0;right:0;z-index:99;background:#0f766e;color:#fff;font:600 17px Segoe UI,Arial;padding:10px 16px;text-align:center';
document.body.appendChild(d);document.body.style.marginTop='44px'}d.textContent=t}"""


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium") if os.path.exists("/opt/pw-browsers/chromium") else p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1280, "height": 720}, record_video_dir=os.path.join(HERE, "video"),
                                  record_video_size={"width": 1280, "height": 720})
        page = ctx.new_page()
        page.on("dialog", lambda d: d.accept())
        n = [0]

        def say(text, wait=1.6, shot=None):
            page.evaluate(CAPTION_JS, text)
            time.sleep(wait)
            if shot:
                page.screenshot(path=os.path.join(SHOTS, shot))

        def tab(name):
            page.click(f'nav a:text-is("{name}")'); time.sleep(1.2)

        page.goto(URL); time.sleep(1)
        say("DukaTrack: forecast what to stock before it runs out", 2.2, "00-home.png")
        page.click('nav a:text-is("Log in")'); time.sleep(1.0)
        say("The login page", 1.4, "01-login.png")

        # ---- Shop Attendant
        say("FR02: the Shop Attendant logs in. A wrong password is refused.", 1.0)
        page.fill("#username", "amina"); page.fill("#password", "wrong-password"); page.click("#login-form button"); time.sleep(1.4)
        say("Wrong password: refused", 1.2, "02-wrong-password.png")
        page.fill("#password", "Attendant@123"); page.click("#login-form button"); time.sleep(1.5)
        say("The Shop Attendant sees only three screens: Enter sales, Stock levels, Forecast", 2.2, "03-attendant-sales.png")

        say("FR13: record a sale. The system will not sell more than the stock held.", 1.2)
        page.select_option("#sale-product", label="Sugar 1kg"); page.fill("#sale-qty", "999"); page.click("#sale-form button"); time.sleep(1.4)
        say("999 sugar refused: only what is in stock can be sold", 1.5, "04-stock-check.png")
        page.fill("#sale-qty", "2"); page.click("#sale-form button"); time.sleep(0.8)
        page.select_option("#sale-product", label="Fresh milk 500ml"); page.fill("#sale-qty", "3"); page.click("#sale-form button"); time.sleep(0.8)
        page.select_option("#sale-product", label="Soda 500ml"); page.fill("#sale-qty", "1"); page.click("#sale-form button"); time.sleep(0.8)
        say("Items added to the sale", 1.4, "05-basket.png")
        page.click("#save-sale"); time.sleep(1.6)
        say("Sale saved. Stock is reduced and the sale is recorded with the time.", 2.0, "06-sale-saved.png")

        say("FR20 and FR18: the Shop Attendant views stock and the forecast (read-only)", 1.2)
        tab("Stock levels"); say("FR20: stock levels (read-only)", 2.0, "07-attendant-stock.png")
        tab("Forecast"); say("FR18: forecast view (no Generate button for the Attendant)", 2.2, "08-attendant-forecast.png")
        page.click("#logout"); time.sleep(1.2)
        say("FR06: the Shop Attendant logs out", 1.4)

        # ---- Shop Owner
        page.fill("#username", "owner"); page.fill("#password", "Owner@123")
        say("FR01: the Shop Owner logs in", 1.0); page.click("#login-form button"); time.sleep(1.6)
        say("FR19 and FR21: stock levels and the low-stock list", 2.4, "09-owner-stock.png")

        tab("Enter goods")
        say("FR12: record stock-in when goods arrive", 1.2)
        page.select_option("#goods-product", label="Maize flour 2kg"); page.fill("#goods-qty", "120"); page.fill("#goods-supplier", "Unga Wholesalers")
        page.screenshot(path=os.path.join(SHOTS, "10-enter-goods.png")); page.click("#goods-form button"); time.sleep(1.8)
        say("Stock-in saved: the stock level goes up", 1.6)

        tab("Forecast")
        say("FR15: the Shop Owner generates the forecast from the shop's own sales history", 1.6)
        page.click("#run"); page.wait_for_selector("#run:not([disabled])", timeout=60000); time.sleep(1.5)
        say("FR17: predicted demand for the next 7 days beside stock now", 2.8, "11-owner-forecast.png")
        page.select_option("#period", "30"); time.sleep(0.8)
        page.click("#run"); page.wait_for_selector("#run:not([disabled])", timeout=60000); time.sleep(1.5)
        say("The same for the next 30 days", 2.4, "12-forecast-30.png")

        tab("Sales")
        say("FR14: the Shop Owner cancels a wrongly entered sale; the items go back to stock", 1.6, "13-owner-sales.png")
        page.click('button:text-is("Cancel sale")'); time.sleep(1.8)
        say("Sale cancelled and stock returned", 1.6, "14-cancelled.png")

        tab("Reports")
        say("FR22 and FR23: sales report for a day, week or month, with CSV export", 2.4, "15-reports.png")
        page.select_option("#report-period", "month"); time.sleep(1.2)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        say("FR24: forecast accuracy (mean absolute error) for finished periods", 2.8, "16-accuracy.png")

        tab("Products")
        say("FR07 to FR11: categories, products, prices and reorder levels", 1.4)
        page.fill("#product-name", "Salt 500g"); page.select_option("#product-category", label="Staples"); page.fill("#product-price", "45")
        page.fill("#product-stock", "40"); page.fill("#product-reorder", "10"); page.screenshot(path=os.path.join(SHOTS, "17-products.png"))
        page.click("#product-form button"); time.sleep(1.8)
        say("FR08: new product added", 1.6)

        tab("Attendants")
        say("FR03 and FR04: create and deactivate Shop Attendant accounts", 1.4)
        page.fill("#att-name", "Joy Achieng"); page.fill("#att-phone", "0700123456"); page.fill("#att-username", "joy"); page.fill("#att-password", "Temp1234")
        page.click("#attendant-form button"); time.sleep(1.6)
        say("FR03: account created (only the password hash is stored)", 2.0, "18-accounts.png")

        tab("Backup")
        say("FR16: back up all data into a protected file", 1.2)
        page.click("#backup-button"); time.sleep(1.8)
        say("Backup saved and logged", 2.2, "19-backup.png")
        page.click("#logout"); time.sleep(1.0)
        say("FR05: the Shop Owner logs out. End of demo.", 2.2)

        video = page.video
        ctx.close()
        path = video.path()
        browser.close()
    dest = os.path.join(HERE, "dukatrack-demo.webm")
    shutil.move(path, dest)
    shutil.rmtree(os.path.join(HERE, "video"), ignore_errors=True)
    print("saved", dest)


if __name__ == "__main__":
    run()
