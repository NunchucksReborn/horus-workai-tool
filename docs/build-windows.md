# Build Athena.exe cho Windows

Tài liệu này hướng dẫn build `Athena.exe` (~50MB zip) thông qua GitHub Actions.

## Quy trình build

### Cách 1: Tự động (khuyến nghị) — khi push tag version

```bash
# 1. Đảm bảo code đã được commit + push lên main
git add . && git commit -m "Release v1.0.33"
git push origin main

# 2. Tạo tag version (format: vMAJOR.MINOR.PATCH)
git tag v1.0.33
git push origin v1.0.33

# 3. Đợi 5-10 phút để GitHub Actions build xong
# 4. Vào GitHub → tab Actions → chọn workflow run "Build Windows EXE"
# 5. Download artifact "Athena-v1.0.33.zip" ở cuối trang run
#    HOẶC vào Releases page để thấy release mới auto-created
```

### Cách 2: Trigger thủ công từ GitHub UI

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
