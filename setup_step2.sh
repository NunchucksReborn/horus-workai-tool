#!/usr/bin/env bash
# Athena Assistant — Step 2: cài system deps + Python deps
# Chạy từ Konsole trên Bazzite, KHÔNG phải opencode Flatpak
set -uo pipefail
CTR=athena

echo "=== [1/5] Cài GTK/WebKit cho pywebview ==="
podman exec -e DEBIAN_FRONTEND=noninteractive "$CTR" bash -lc '
  dnf install -y --setopt=fastestmirror=True --setopt=max_parallel_downloads=20 --nodocs \
    webkit2gtk4.1 webkit2gtk4.1-devel gtk3-devel \
    gobject-introspection-devel dbus-libs gcc make 2>&1 | tail -10
'

echo "=== [2/5] Cài Chromium deps cho playwright ==="
podman exec -e DEBIAN_FRONTEND=noninteractive "$CTR" bash -lc '
  dnf install -y --setopt=fastestmirror=True --setopt=max_parallel_downloads=20 --nodocs \
    nss fontconfig freetype alsa-lib pango cairo gdk-pixbuf2 \
    libdrm libxkbcommon mesa-libgbm at-spi2-atk \
    libXtst libXrandr libXcomposite libXdamage libXfixes 2>&1 | tail -10
'

echo "=== [3/5] Cài pip + git ==="
podman exec -e DEBIAN_FRONTEND=noninteractive "$CTR" bash -lc '
  dnf install -y --setopt=fastestmirror=True --setopt=max_parallel_downloads=20 --nodocs \
    python3-pip git 2>&1 | tail -5
'

echo "=== [4/5] Tạo Python venv + pip install Athena deps ==="
podman exec -e DEBIAN_FRONTEND=noninteractive "$CTR" bash -lc "
  cd /run/media/system/home/Horus/horus-workai-tool
  python3.11 -m venv .venv
  source .venv/bin/activate
  python -m pip install --upgrade pip wheel 2>&1 | tail -3
  pip install --quiet \
    'fastapi>=0.110' 'uvicorn[standard]' 'pywebview' \
    'python-multipart' 'pydantic>=2' 'requests' \
    'playwright' 'python-dotenv' 'httpx' 'pydantic-settings' 2>&1 | tail -10
  echo '--- pip list ---'
  pip list 2>/dev/null | grep -iE 'fastapi|uvicorn|webview|playwright|pydantic|httpx'
"

echo "=== [5/5] Playwright install chromium ==="
podman exec -e DEBIAN_FRONTEND=noninteractive "$CTR" bash -lc "
  cd /run/media/system/home/Horus/horus-workai-tool
  source .venv/bin/activate
  playwright install chromium 2>&1 | tail -5
  echo '--- Playwright browsers ---'
  ls -la ~/.cache/ms-playwright/ 2>/dev/null | head -5
"

echo ""
echo "=== XONG! Để chạy GUI: ==="
echo "  distrobox enter athena"
echo "  cd /run/media/system/home/Horus/horus-workai-tool"
echo "  source .venv/bin/activate"
echo "  python main.py"
