#!/bin/bash
# alphafix.sh — Re-encode alpha files with Apple's native ProRes encoder
#
# Run this ON YOUR MAC after record.js finishes inside Docker.
#
# FFmpeg's prores_ks (Linux) produces ProRes 4444 files where the alpha channel
# is not recognized by Apple Silicon's hardware ProRes decoder on macOS Sonoma 14.4+.
# The alpha data is correct, but the container atoms aren't flagged the way Apple expects.
#
# Fix: re-encode using prores_videotoolbox (Apple's hardware encoder) which produces
# correctly-flagged alpha that Resolve, FCP, and Premiere all recognize natively.

cd "$(dirname "$0")"

OUTPUT_DIR="$(pwd)/HTML Files/Output"

if ! ffmpeg -hide_banner -encoders 2>/dev/null | grep -q prores_videotoolbox; then
  echo "ERROR: prores_videotoolbox not available."
  echo "This script must run on macOS with ffmpeg installed (brew install ffmpeg)."
  exit 1
fi

echo "Re-encoding alpha files with Apple ProRes encoder..."
echo ""

for alpha_file in "$OUTPUT_DIR"/*_alpha.mov; do
  [ -f "$alpha_file" ] || continue

  base="$(basename "$alpha_file")"
  tmp_file="${alpha_file%.mov}_vt.mov"

  echo "  $base ..."
  if ffmpeg -y -i "$alpha_file" \
    -c:v prores_videotoolbox -profile:v 4 -pix_fmt yuva444p10le \
    "$tmp_file" 2>/dev/null; then
    mv "$tmp_file" "$alpha_file"
    echo "  ✓ $base — $(du -h "$alpha_file" | cut -f1)"
  else
    echo "  ✗ Failed: $base (keeping original)"
    rm -f "$tmp_file"
  fi
done

echo ""
echo "Done."
ls -lh "$OUTPUT_DIR"/*_alpha.mov 2>/dev/null
