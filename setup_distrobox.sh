#!/usr/bin/env bash
# Athena Assistant — setup & run trên BazziteOS qua distrobox
# Chạy script này từ terminal thật trên host (KHÔNG phải trong Flatpak/opencode)
# Usage: bash setup_distrobox.sh

set -euo pipefail

PROJECT_DIR="/run/media/system/home/Horus/horus-workai-tool"
CONTAINER_NAME="athena"
IMAGE="quay.io/fedora/fedora:latest"

echo "=== [1/7] Kiểm tra distrobox + podman ==="
if ! command -v distrobox >/dev/null 2>&1; then
  echo "distrobox CHƯA có. Đang cài..."
  # Bazzite thường đã cài sẵn distrobox, fallback nếu thiếu
  if command -v rpm-ostree >/dev/null 2>&1; then
    rpm-ostree install --assumeyes distrobox || { echo "Không thể cài distrobox qua rpm-ostree"; exit 1; }
  else
    echo "Cài thủ công: https://github.com/89luca89/distrobox#installation"
    exit 1
  fi
fi
if ! command -v podman >/dev/null 2>&1; then
  echo "podman CHƯA có. Đang cài..."
  rpm-ostree install --assumeyes podman || { echo "Không thể cài podman"; exit 1; }
  echo "REBOOT hoặc re-login sau bước này rồi chạy lại script."
  exit 0
fi

echo "=== [2/7] Tạo distrobox '${CONTAINER_NAME}' (Fedora latest) ==="
if distrobox list 2>/dev/null | grep -q "^${CONTAINER_NAME}\b"; then
  echo "Container đã tồn tại, bỏ qua tạo."
else
  distrobox create \
    --name "${CONTAINER_NAME}" \
    --image "${IMAGE}" \
    --yes \
    --nvidia  # bỏ --nvidia nếu không có GPU NVIDIA
fi

echo "=== [3/7] Bind-mount project folder vào container ==="
# distrobox đã auto-bind home. Project ở /run/media (external drive)
# cần bind thêm nếu distrobox chưa tự thấy
distrobox enter "${CONTAINER_NAME}" -- \
  bash -c "ls '${PROJECT_DIR}' >/dev/null 2>&1 || {
    echo 'Project dir không thấy từ container, kiểm tra lại path';
    exit 1;
  }"

echo "=== [4/7] Cài system deps cho pywebview (GTK) + Playwright ==="
distrobox enter "${CONTAINER_NAME}" -- sudo dnf install -y \
  python3.11 python3.11-devel python3.11-virtualenv \
  webkit2gtk4.1 webkit2gtk4.1-devel \
  gtk3-devel gobject-introspection-devel \
  libgcc libstdc++ nss fontconfig freetype \
  dbus-libs at-spi2-atk libdrm libxkbcommon mesa-libgbm \
  alsa-lib pango cairo gdk-pixbuf2 \
  || { echo "Cài system deps thất bại"; exit 1; }

echo "=== [5/7] Tạo Python venv + cài pip deps ==="
distrobox enter "${CONTAINER_NAME}" -- bash <<EOF
set -euo pipefail
cd '${PROJECT_DIR}'
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip wheel
pip install \
  "fastapi>=0.110" "uvicorn[standard]" "pywebview" \
  "python-multipart" "pydantic>=2" "requests" \
  "playwright" "python-dotenv" "httpx" \
  "pydantic-settings"
echo "--- pip list (liên quan) ---"
pip list | grep -iE "fastapi|uvicorn|webview|playwright|pydantic"
EOF

echo "=== [6/7] Cài Chromium cho Playwright (submitter.py dùng) ==="
distrobox enter "${CONTAINER_NAME}" -- bash <<EOF
set -euo pipefail
cd '${PROJECT_DIR}'
source .venv/bin/activate
playwright install chromium
echo "Playwright browsers:"
ls -la ~/.cache/ms-playwright/ 2>/dev/null | head -5
EOF

echo "=== [7/7] Verify + chạy thử (foreground) ==="
echo ""
echo "Tất cả đã sẵn sàng!"
echo ""
echo "Để chạy GUI tool, mỗi lần dùng:"
echo "  distrobox enter athena"
echo "  cd '${PROJECT_DIR}'"
echo "  source .venv/bin/activate"
echo "  python main.py"
echo ""
echo "(Tuỳ chọn) Tạo wrapper script trên host để chạy 1 lệnh:"
cat <<WRAPPER
  cat > ~/.local/bin/athena <<'E'
#!/usr/bin/env bash
exec distrobox enter athena -- bash -lc "cd '${PROJECT_DIR}' && source .venv/bin/activate && exec python main.py"
E
  chmod +x ~/.local/bin/athena
WRAPPER
