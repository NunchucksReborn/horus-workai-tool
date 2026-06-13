import os
import sys
import json
import argparse
import time as _time
from playwright.sync_api import sync_playwright

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

STATUS_FILE = "preview_status.json"
PREVIEW_DATA_FILE = "preview_tasks.json"
PREVIEW_EDIT_FILE = "preview_tasks_edit.json"

def update_status(status, current, total, msg):
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump({"status": status, "current": current, "total": total, "msg": msg}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARNING] Failed to write status: {e}")

def load_env(path=".env"):
    env = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env

# Set browsers path for PyInstaller frozen app or local execution
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(bundle_dir, "ms-playwright")
else:
    local_ms_playwright = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ms-playwright")
    if os.path.exists(local_ms_playwright):
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = local_ms_playwright

def login(page, username, password):
    print("Logging in...")
    page.goto("https://workai.horus.io.vn/", timeout=15000)
    page.wait_for_load_state("networkidle")
    page.fill('input[name="login"]', username)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_timeout(3000)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    print("[OK] Logged in.\n")

def navigate_to_timeline(page):
    page.goto("https://workai.horus.io.vn/timeline-schedule", timeout=15000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)
    print("[OK] On Daily Time Allocation page.\n")

def close_all_overlays(page):
    for _ in range(2):
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)

def open_issue_sheet(page, issue_key):
    print(f"Waiting for card {issue_key} to render on board...")
    try:
        page.wait_for_selector(f'span:has-text("{issue_key}")', timeout=12000)
    except Exception as e:
        return False, f"Không tìm thấy thẻ công việc {issue_key} trên Timeline"

    # Click to open sheet
    card_loc = page.locator(f'span:has-text("{issue_key}")').first
    try:
        card_loc.click(timeout=3000)
    except Exception:
        try:
            card_loc.evaluate("el => el.click()")
        except Exception as click_err:
            return False, f"Không thể click vào thẻ công việc {issue_key}: {str(click_err)}"

    # Wait for sheet content to appear
    sheet_opened = False
    for _ in range(10):
        page.wait_for_timeout(300)
        has_sheet = page.evaluate("""
            () => {
                const sheet = document.querySelector('[data-slot="sheet-content"]')
                           || document.querySelector('[data-state="open"][role="dialog"]');
                return !!sheet;
            }
        """)
        if has_sheet:
            sheet_opened = True
            break
            
    if not sheet_opened:
        return False, "Không thể mở bảng chi tiết công việc"
        
    page.wait_for_timeout(500)
    return True, ""

def do_scan(page, tasks):
    total = len(tasks)
    scanned_results = []
    
    for idx, t in enumerate(tasks, 1):
        issue_key = t.get("issue_key")
        title_local = t.get("title", "")
        project = t.get("project", "")
        
        if not issue_key:
            print(f"[{idx}/{total}] Bỏ qua task không có issue_key: {title_local[:30]}")
            scanned_results.append({
                "issue_key": "",
                "project": project,
                "title": title_local,
                "description": t.get("description", ""),
                "acceptance_criteria": t.get("acceptance_criteria", ""),
                "error": "Chưa được nhập lên WorkAI"
            })
            continue
            
        print(f"[{idx}/{total}] Đang quét {issue_key}...")
        update_status("running", idx - 1, total, f"Đang quét công việc {idx}/{total}: {issue_key}...")
        
        ok, err = open_issue_sheet(page, issue_key)
        if not ok:
            print(f"         ⚠ Lỗi: {err}")
            scanned_results.append({
                "issue_key": issue_key,
                "project": project,
                "title": title_local,
                "description": "",
                "acceptance_criteria": "",
                "error": err
            })
            close_all_overlays(page)
            continue
            
        # Extract fields via Page Evaluate
        details = page.evaluate("""
            () => {
                const sheet = document.querySelector('[data-slot="sheet-content"]')
                           || document.querySelector('[data-state="open"][role="dialog"]');
                if (!sheet) return null;
                
                const summaryInput = sheet.querySelector('input[name="summary"]');
                const descTextarea = sheet.querySelector('textarea[name="description"]');
                const acTextarea = sheet.querySelector('textarea[name="acceptance_criteria"]');
                
                return {
                    title: summaryInput ? summaryInput.value : '',
                    description: descTextarea ? descTextarea.value : '',
                    acceptance_criteria: acTextarea ? acTextarea.value : ''
                };
            }
        """)
        
        close_all_overlays(page)
        
        if details:
            print(f"         ✓ Quét thành công: {details['title'][:30]}...")
            scanned_results.append({
                "issue_key": issue_key,
                "project": project,
                "title": details.get("title") or title_local,
                "description": details.get("description") or "",
                "acceptance_criteria": details.get("acceptance_criteria") or ""
            })
        else:
            print(f"         ⚠ Lỗi: Không đọc được các trường nhập liệu")
            scanned_results.append({
                "issue_key": issue_key,
                "project": project,
                "title": title_local,
                "description": "",
                "acceptance_criteria": "",
                "error": "Không tìm thấy trường nhập liệu trong modal"
            })
            
    # Save results to file
    with open(PREVIEW_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(scanned_results, f, ensure_ascii=False, indent=2)
        
    update_status("success", total, total, "Đã hoàn thành quét nội dung từ WorkAI!")
    print("\n[SUCCESS] Hoàn thành quét tất cả các công việc.")

def do_update(page, tasks):
    total = len(tasks)
    
    for idx, t in enumerate(tasks, 1):
        issue_key = t.get("issue_key")
        title = t.get("title")
        description = t.get("description")
        acceptance_criteria = t.get("acceptance_criteria")
        
        if not issue_key:
            print(f"[{idx}/{total}] Bỏ qua task không có issue_key")
            continue
            
        print(f"[{idx}/{total}] Đang cập nhật {issue_key}...")
        update_status("running", idx - 1, total, f"Đang cập nhật công việc {idx}/{total}: {issue_key}...")
        
        ok, err = open_issue_sheet(page, issue_key)
        if not ok:
            print(f"         ⚠ Lỗi: {err}")
            update_status("error", idx - 1, total, f"Lỗi ở {issue_key}: {err}")
            close_all_overlays(page)
            raise Exception(err)
            
        # Fill fields via Page Evaluate to trigger React change events correctly
        changed = page.evaluate("""
            ([t, desc, ac]) => {
                const sheet = document.querySelector('[data-slot="sheet-content"]')
                           || document.querySelector('[data-state="open"][role="dialog"]');
                if (!sheet) return false;
                
                const summaryInput = sheet.querySelector('input[name="summary"]');
                const descTextarea = sheet.querySelector('textarea[name="description"]');
                const acTextarea = sheet.querySelector('textarea[name="acceptance_criteria"]');
                
                let changed = false;
                if (t !== null && t !== undefined && summaryInput && summaryInput.value !== t) {
                    summaryInput.value = t;
                    summaryInput.dispatchEvent(new Event('input', { bubbles: true }));
                    summaryInput.dispatchEvent(new Event('change', { bubbles: true }));
                    changed = true;
                }
                if (desc !== null && desc !== undefined && descTextarea && descTextarea.value !== desc) {
                    descTextarea.value = desc;
                    descTextarea.dispatchEvent(new Event('input', { bubbles: true }));
                    descTextarea.dispatchEvent(new Event('change', { bubbles: true }));
                    changed = true;
                }
                if (ac !== null && ac !== undefined && acTextarea && acTextarea.value !== ac) {
                    acTextarea.value = ac;
                    acTextarea.dispatchEvent(new Event('input', { bubbles: true }));
                    acTextarea.dispatchEvent(new Event('change', { bubbles: true }));
                    changed = true;
                }
                return changed;
            }
        """, [title, description, acceptance_criteria])
        
        print(f"         Fields changed: {changed}")
        
        # Click Lưu / Cập nhật
        page.wait_for_timeout(300)
        save_btn = page.locator('[data-slot="sheet-content"] button:has-text("Cập nhật"), [data-slot="sheet-content"] button:has-text("Lưu"), [role="dialog"] button:has-text("Cập nhật"), [role="dialog"] button:has-text("Lưu"), button:has-text("Cập nhật"), button:has-text("Lưu")').first
        if save_btn.count() > 0 and save_btn.is_visible():
            print("         Clicking Cập nhật/Lưu...")
            save_btn.click()
            page.wait_for_timeout(1000)
        else:
            print("         Assuming autosave on blur/close.")
            page.wait_for_timeout(800)
            
        close_all_overlays(page)
        page.wait_for_timeout(300)
        print(f"         ✓ Cập nhật thành công {issue_key}")
        
    update_status("success", total, total, "Đã hoàn thành cập nhật các công việc lên WorkAI!")
    print("\n[SUCCESS] Hoàn thành cập nhật tất cả các công việc.")

def main():
    parser = argparse.ArgumentParser(description="WorkAI Preview Helper")
    parser.add_argument("--mode", choices=["scan", "update"], required=True, help="Chế độ quét (scan) hoặc cập nhật (update)")
    args = parser.parse_args()
    
    if args.mode == "scan":
        input_file = "tasks.json" # local tasks
        if not os.path.exists(input_file):
            print(f"[ERROR] '{input_file}' not found.")
            sys.exit(1)
            
        with open(input_file, "r", encoding="utf-8") as f:
            local_tasks = json.load(f)
            
        # Match with submitted.json to get issue_key
        submitted_file = "submitted.json"
        import hashlib
        def get_fp(t):
            key = f"{t.get('project','')}|{t.get('title','')}|{t.get('date','')}"
            return hashlib.md5(key.encode('utf-8')).hexdigest()
            
        submitted = {}
        if os.path.exists(submitted_file):
            with open(submitted_file, "r", encoding="utf-8") as sf:
                submitted = json.load(sf)
                
        tasks_to_scan = []
        for t in local_tasks:
            fp = get_fp(t)
            issue_key = ""
            if fp in submitted:
                issue_key = submitted[fp].get("issue_key", "")
            tasks_to_scan.append({
                "project": t.get("project", ""),
                "title": t.get("title", ""),
                "description": t.get("description", ""),
                "acceptance_criteria": t.get("acceptance_criteria", ""),
                "issue_key": issue_key
            })
            
        total = len(tasks_to_scan)
        if total == 0:
            print("Không có task nào để quét.")
            update_status("success", 0, 0, "Không có công việc nào cần quét.")
            sys.exit(0)
            
        tasks = tasks_to_scan
    else: # mode == "update"
        if not os.path.exists(PREVIEW_EDIT_FILE):
            print(f"[ERROR] '{PREVIEW_EDIT_FILE}' not found.")
            sys.exit(1)
        with open(PREVIEW_EDIT_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)
        total = len(tasks)
        if total == 0:
            print("Không có task nào cần cập nhật.")
            update_status("success", 0, 0, "Không có công việc nào cần cập nhật.")
            sys.exit(0)

    env = load_env()
    username = env.get("WORKAI_USERNAME")
    password = env.get("WORKAI_PASSWORD")
    if not username or not password:
        print("[ERROR] Missing credentials in .env")
        update_status("error", 0, total, "Thiếu thông tin tài khoản WorkAI trong cấu hình.")
        sys.exit(1)

    print(f"Khởi chạy Playwright chế độ: {args.mode}...")
    update_status("running", 0, total, "Đang đăng nhập vào WorkAI...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            login(page, username, password)
            navigate_to_timeline(page)
            
            if args.mode == "scan":
                do_scan(page, tasks)
            else:
                do_update(page, tasks)
                
            browser.close()
            sys.exit(0)
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            page.screenshot(path=f"error_preview_{args.mode}.png")
            update_status("error", 0, total, f"Lỗi: {str(e)}")
            browser.close()
            sys.exit(1)

if __name__ == "__main__":
    main()
