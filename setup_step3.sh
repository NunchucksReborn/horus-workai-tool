#!/usr/bin/env bash
# Athena Assistant — Step 3: cài pygobject + qtpy (Python GUI bindings)
set -uo pipefail
CTR=athena

echo "=== [1/2] Cài pygobject cho GTK backend ==="
podman exec -e DEBIAN_FRONTEND=noninteractive "$CTR" bash -lc '
  source /run/media/system/home/Horus/horus-workai-tool/.venv/bin/activate
  pip install --quiet pygobject pyqt6 qtpy 2>&1 | tail -10
  echo "--- verify ---"
  python -c "import gi; gi.require_version(\"Gtk\", \"3.0\"); gi.require_version(\"WebKit2\", \"4.1\"); from gi.repository import Gtk, WebKit2; print(\"GTK+WebKit OK\")" 2>&1
'

echo "=== [2/2] Test pywebview launch (10s timeout) ==="
podman exec -e DEBIAN_FRONTEND=noninteractive "$CTR" bash -lc '
  source /run/media/system/home/Horus/horus-workai-tool/.venv/bin/activate
  cd /run/media/system/home/Horus/horus-workai-tool
  # Quick test: load static page, auto-close sau 5s
  timeout 10 python -c "
import webview, threading, time
t = threading.Thread(target=lambda: (time.sleep(5), webview.destroy_window() if webview.windows else None), daemon=True)
t.start()
webview.create_window(\"Test\", \"data:text/html,<h1 style=\\\"color:red\\\">Athena OK</h1>\", width=400, height=300)
try:
    webview.start()
    print(\"pywebview started OK\")
except Exception as e:
    print(\"pywebview FAIL:\", e)
" 2>&1 | tail -20
'
