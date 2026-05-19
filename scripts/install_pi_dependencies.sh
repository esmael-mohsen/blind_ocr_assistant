#!/usr/bin/env bash
set -euo pipefail

echo "Phase 11: Raspberry Pi dependency setup guidance"
echo "This script is idempotent and does not enable service startup automatically."

if command -v python3 >/dev/null 2>&1; then
  echo "python3: present"
else
  echo "python3: missing; install python3 and python3-venv"
fi

if command -v espeak-ng >/dev/null 2>&1; then
  echo "espeak-ng: present"
else
  echo "espeak-ng: missing; install for local spoken output"
fi

if command -v tesseract >/dev/null 2>&1; then
  echo "tesseract: present"
else
  echo "tesseract: missing; install with ara and eng language data"
fi

echo "Optional packages may include OpenCV, PaddleOCR, Vosk, and Orbbec/OpenNI2 drivers."
echo "Run scripts/pi_deployment_check.py --full after installation."
