import json
import os
import time
from pathlib import Path

AUTH_FILE = Path(".ds_auth.json")

def load_auth():
    if AUTH_FILE.exists():
        try:
            with open(AUTH_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def save_auth(token: str, cookies: str):
    with open(AUTH_FILE, "w") as f:
        json.dump({"token": token, "cookies": cookies}, f, indent=4)

def logout():
    if AUTH_FILE.exists():
        AUTH_FILE.unlink()
        return True
    return False

def interactive_login():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("\n[Error] Playwright is not installed. Please run: pip install playwright")
        print("        And then run: playwright install chromium\n")
        return False
        
    print("\n[System] Launching browser for login...")
    print("[System] Please log in manually and solve any Cloudflare CAPTCHAs.")
    print("[System] Waiting for successful authentication (Auto-extraction in progress)...\n")

    with sync_playwright() as p:
        # Use stealth arguments to bypass basic anti-bot checks
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        )
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        
        # Hide automation script traces
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = context.new_page()
        page.goto("https://chat.deepseek.com/sign_in")
        
        extracted_token = None
        
        # Poll LocalStorage for the Bearer token
        timeout = 300 # Wait up to 5 minutes for user to login
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # We search all localStorage keys to find the one containing a Bearer token
                ls_data = page.evaluate("() => JSON.stringify(localStorage)")
                if ls_data:
                    ls_dict = json.loads(ls_data)
                    for key, val in ls_dict.items():
                        if "Bearer ey" in str(val):
                            # It could be a direct string or a JSON object string
                            if isinstance(val, str) and val.startswith('{"'):
                                try:
                                    parsed_val = json.loads(val)
                                    if "value" in parsed_val and "Bearer " in parsed_val["value"]:
                                        extracted_token = parsed_val["value"]
                                        break
                                except:
                                    pass
                            elif "Bearer ey" in val:
                                extracted_token = val
                                break
                                
                if extracted_token:
                    break
            except Exception as e:
                pass
                
            time.sleep(1.5)
            
        if not extracted_token:
            print("\n[Error] Login timed out or token not found. Please try again.")
            browser.close()
            return False
            
        # Wait a moment for cookies to fully settle
        time.sleep(2)
        
        # Extract Cookies
        cookies = context.cookies("https://chat.deepseek.com")
        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        
        browser.close()
        
        # Save credentials
        save_auth(extracted_token, cookie_str)
        print("\n[Success] Authentication successful! Tokens extracted and saved securely.")
        return True

if __name__ == "__main__":
    interactive_login()
