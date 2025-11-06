from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Start directly on the page with the table
    page.goto("https://cas.duffandphelps.com/Correspondence/MailCorrespondence")  # Replace with your actual URL
    input("Press Enter to close the browser")
    print("Page title", page.title())
    browser.close()
