#!/usr/bin/env python3
"""Bundle the template, styles, script and Japanese audio into one HTML file."""
from __future__ import annotations

import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "src" / "template.html"
STYLES = ROOT / "src" / "styles.css"
APP = ROOT / "src" / "app.js"
KANA = ROOT / "src" / "kana.json"
MANIFEST = ROOT / "build" / "audio_manifest.json"
OUTPUT = ROOT / "五十音听写.html"


def main() -> None:
    data = json.loads(KANA.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    audio: dict[str, dict[str, dict[str, str]]] = {}
    total_bytes = 0
    for voice, variants in manifest.items():
        audio[voice] = {}
        for variant, items in variants.items():
            audio[voice][variant] = {}
            for kana, info in items.items():
                raw = (ROOT / info["file"]).read_bytes()
                total_bytes += len(raw)
                audio[voice][variant][kana] = (
                    "data:audio/mpeg;base64,"
                    + base64.b64encode(raw).decode("ascii")
                )

    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    audio_json = json.dumps(audio, ensure_ascii=False, separators=(",", ":"))
    css = STYLES.read_text(encoding="utf-8")
    app = APP.read_text(encoding="utf-8")

    html = TEMPLATE.read_text(encoding="utf-8")
    html = html.replace("/*__STYLES__*/", css)
    html = html.replace("/*__KANA_DATA__*/", data_json)
    html = html.replace("/*__KANA_AUDIO__*/", audio_json)
    html = html.replace("/*__APP__*/", app)

    unresolved = [
        token
        for token in ("__STYLES__", "__KANA_DATA__", "__KANA_AUDIO__", "__APP__")
        if token in html
    ]
    if unresolved:
        raise RuntimeError(f"unresolved template tokens: {unresolved}")
    if "</script" in audio_json or "</script" in data_json:
        raise RuntimeError("unexpected </script> in embedded data")

    OUTPUT.write_text(html, encoding="utf-8")
    print(
        f"wrote {OUTPUT.name}: {OUTPUT.stat().st_size / 1024 / 1024:.2f} MB "
        f"(audio {total_bytes / 1024:.0f} KB, {sum(len(v) for vv in audio.values() for v in vv.values())} clips)"
    )


if __name__ == "__main__":
    main()
