# Build Athena.exe cho Windows

Có 2 cách build: tự động qua **GitHub Actions** (cần tài khoản trả phí / repo public) hoặc **thủ công trên máy Windows** (miễn phí, dùng script tự động).

## Cách 1: Thủ công trên máy Windows (khuyến nghị — miễn phí)

### Chuẩn bị

1. **Cài Python 3.11** trên máy Windows:
   - Tải từ https://www.python.org/downloads/
   - **QUAN TRỌNG**: Ở bước đầu tiên, đánh dấu **"Add Python to PATH"** rồi bấm Install Now
2. **Copy project** vào máy Windows (USB / GitHub / Zalo)

### Build

1. Mở File Explorer, vào folder project
2. **Double-click file `build-windows.bat`**
3. Chờ script chạy ~5-10 phút (tự động cài Python deps + Playwright Chromium + build exe)
4. Khi xong, file `dist\Athena.exe` xuất hiện trong folder project
5. Copy `dist\Athena.exe` cho user

### Cần giúp đỡ?

- Xem chi tiết từng bước: [Chi tiết build thủ công](#chi-tiết-build-thủ-công)
- Hoặc dùng GitHub Actions: [Cách 2: GitHub Actions](#cách-2-github-actions-tự-động)

## Chi tiết build thủ công

Nếu `build-windows.bat` gặp lỗi, bạn có thể chạy thủ công:

```cmd
REM Mở Command Prompt trong folder project
python -m venv .venv
.venv\Scripts\activate
pip install fastapi "uvicorn[standard]" pywebview python-multipart "pydantic>=2" requests playwright python-dotenv httpx pyinstaller
playwright install chromium

REM Copy ms-playwright vao project root
xcopy "%USERPROFILE%\AppData\Local\ms-playwright" "ms-playwright\" /E /I /Q /Y

REM Build
pyinstaller main.spec --noconfirm --clean

REM Rename
ren dist\main.exe Athena.exe
```

## Cách 2: GitHub Actions (tự động)

> Cần tài khoản GitHub trả phí HOẶC repo public. Nếu gặp lỗi "account is locked due to a billing issue" thì dùng Cách 1.

### Trigger build

**Cách 2A — Push tag version (tự động):**

```bash
git tag v1.0.33
git push origin v1.0.33
```

Workflow tự chạy, khi xong sẽ tự tạo GitHub Release với file `.zip` đính kèm.

**Cách 2B — Trigger thủ công từ GitHub UI:**

1. Vào GitHub repo → tab **Actions**
2. Chọn workflow **"Build Windows EXE"** ở sidebar trái
3. Bấm nút **"Run workflow"** → chọn branch → bấm **"Run workflow"**
4. Đợi 5-10 phút
5. Download artifact ở cuối trang run

## Workflow CI/CD

| Trigger | Hành động |
|---|---|
| Push tag `v*.*.*` | Build + auto-attach `.zip` vào GitHub Release |
| Manual (workflow_dispatch) | Build + upload artifact (giữ 30 ngày) |
| Push lên main (không có tag) | KHÔNG build (chỉ update code, user auto-update qua app) |

## Output

- **Filename**: `Athena-v1.0.33.zip`
- **Size**: ~50MB (zip), ~476MB khi giải nén (gồm `Athena.exe` + bundle Python runtime)
- **Platform**: Windows 10/11 64-bit (cần WebView2 — đã có sẵn trên Win 10+)

## Yêu cầu từ user cuối

- Windows 10 hoặc 11
- WebView2 Runtime (mặc định đã cài trên Win 10/11; nếu thiếu tải từ https://developer.microsoft.com/microsoft-edge/webview2/)
- Quyền ghi vào thư mục chứa `Athena.exe` (để lưu `.env`, `config.json`, cached data)

## First-run setup

Lần đầu chạy `Athena.exe`, app sẽ hiện màn hình **Cài đặt** yêu cầu nhập:
- Họ tên + Chức danh
- AI Provider (Gemini / OpenAI / DeepSeek) + API key
- WorkAI username + password
- Cấu hình các nguồn chat (Rocket.Chat, Email, Git...)

Các thông tin này lưu vào `.env` và `config.json` ngay cạnh file `.exe`.

## Troubleshooting

### Antivirus flag false-positive
PyInstaller exe thường bị Windows Defender / antivirus cảnh báo nhầm. Giải pháp:
- Bấm "More info" → "Run anyway" (Windows Defender SmartScreen)
- Hoặc add exception cho folder chứa `Athena.exe`
- Khi phân phối chính thức nên ký số code với certificate (tốn phí)

### WebView2 missing
Nếu app không mở được cửa sổ, tải WebView2 Runtime: https://developer.microsoft.com/microsoft-edge/webview2/

### "Port 8000 already in use"
App cần cổng 8000 trống. Nếu bị chiếm:
- Đóng các app khác dùng cổng 8000
- Hoặc restart máy

### App mở nhưng trắng/trống
- Đợi 3-5s để FastAPI server start (xem console log nếu có)
- Mở browser thủ công: http://127.0.0.1:8000

## Cấu trúc sau khi build

```
Athena-folder/
├── Athena.exe                    (~50MB)
├── .env                          (tạo khi user chạy first-run setup)
├── config.json                   (tạo khi user chạy first-run setup)
├── projects.json                 (tạo khi scan WorkAI lần đầu)
├── chat_raw.json / git_raw.json (cache sync)
├── saved_raw_tasks.json          (cache daily tasks)
├── memorytask.md                 (output Tạo việc)
├── tasks.json                    (output Nhập việc)
├── submitted.json                (log các task đã submit WorkAI)
└── last_sync.txt                 (timestamp sync gần nhất)
```

## Khi nào cần build lại exe

| Thay đổi | Cần build lại exe? |
|---|---|
| Sửa code `.py` / `.html` / `.css` / `.js` | ❌ Không — user auto-update qua app |
| Thêm/sửa pip dependencies | ✅ Có |
| Sửa `main.spec` | ✅ Có |
| Thêm/xóa file bundle trong `datas=[]` | ✅ Có |

## Workflow file location

`.github/workflows/build-windows.yml` — chỉnh sửa workflow tại đây nếu cần thay đổi quy trình build.
