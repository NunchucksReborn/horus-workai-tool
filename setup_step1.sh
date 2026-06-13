#!/usr/bin/env bash
# Athena setup step-by-step (chạy từ Konsole trên Bazzite, KHÔNG phải opencode Flatpak)
# Mỗi lệnh dùng `podman exec` trực tiếp để bypass lỗi distrobox ptsname.
# Nếu 1 lệnh treo >5 phút, Ctrl+C rồi báo lại.

set -uo pipefail
CTR=athena

run_in() {
  podman exec -e "DEBIAN_FRONTEND=noninteractive" "$CTR" bash -lc "$1"
}

echo "=== [A] Cài python3.11 (batch 1, quan trọng nhất) ==="
run_in "dnf install -y --setopt=fastestmirror=False --setopt=max_parallel_downloads=10 --nodocs python3.11 python3.11-devel 2>&1 | tail -15"

echo "=== [B] Verify python3.11 ==="
run_in "python3.11 --version"

echo "=== [C] Cài GTK/WebKit cho pywebview (batch 2) ==="
run_in "dnf install -y --setopt=fastestmirror=False --setopt=max_parallel_downloads=10 --nodocs webkit2gtk4.1 webkit2gtk4.1-devel gtk3-devel gobject-introspection-devel dbus-libs 2>&1 | tail -15"

echo "=== [D] Cài Chromium deps cho playwright (batch 3) ==="
run_in "dnf install -y --setopt=fastestmirror=False --setopt=max_parallel_downloads=10 --nodocs nss fontconfig freetype alsa-lib pango cairo gdk-pixbuf2 libdrm libxkbcommon mesa-libgbm at-spi2-atk 2>&1 | tail -15"

echo "=== [E] Cài pip + git + venv tools (batch 4) ==="
run_in "dnf install -y --setopt=fastestmirror=False --setopt=max_parallel_downloads=10 --nodocs python3-pip git 2>&1 | tail -10"

echo "=== [F] Verify đủ deps ==="
run_in "rpm -q python3.11 webkit2gtk4.1 gtk3-devel nss fontconfig 2>&1"

echo ""
echo "Nếu hết lỗi, tiếp tục chạy: bash ${0##*/} --pip"
echo "Hoặc chạy thủ công:"
echo "  podman exec -it $CTR bash"
echo "  cd /run/media/system/home/Horus/horus-workai-tool"
echo "  python3.11 -m venv .venv && source .venv/bin/activate"
echo "  pip install fastapi 'uvicorn[standard]' pywebview python-multipart 'pydantic>=2' requests playwright python-dotenv httpx"
echo "  playwright install chromium"
echo "  python main.py"
