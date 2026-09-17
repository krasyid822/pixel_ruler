#!/usr/bin/env python3
"""MCP server untuk Pixel Ruler.

Men-serve tool untuk mem-parsing dan menginterpretasi data koordinat
yang disalin dari aplikasi Pixel Ruler. Menjalankan via stdio JSON-RPC,
tanpa dependensi eksternal (stdlib saja).

Format yang dikenali (lihat AGENTS.md):
  - Titik:      (x, y)
  - Area:       (x1=<x>, y1=<y>) (x2=<x>, y2=<y>) ukuran=<w>x<h>px
"""

import json
import re
import sys

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "pixel-ruler-coords"
SERVER_VERSION = "1.0.0"

POINT_RE = re.compile(r"^\((\d+), (\d+)\)$")
AREA_RE = re.compile(
    r"^\(x1=(\d+), y1=(\d+)\) \(x2=(\d+), y2=(\d+)\) ukuran=(\d+)x(\d+)px$"
)


def parse_point(text):
    m = POINT_RE.match(text)
    if not m:
        return None
    return {"kind": "point", "x": int(m[1]), "y": int(m[2])}


def parse_area(text):
    m = AREA_RE.match(text)
    if not m:
        return None
    x1, y1, x2, y2, w, h = (int(g) for g in m.groups())
    if w != x2 - x1 or h != y2 - y1:
        return {
            "kind": "area",
            "error": "ukuran tidak konsisten dengan x2-x1 / y2-y1",
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "width": w, "height": h,
        }
    return {
        "kind": "area",
        "x1": x1, "y1": y1, "x2": x2, "y2": y2,
        "width": w, "height": h,
        "span": [w, h],
        "pixel_count": (w + 1) * (h + 1),
        "center": {"x": (x1 + x2) / 2, "y": (y1 + y2) / 2},
    }


TOOLS = [
    {
        "name": "parse_coordinates",
        "description": (
            "Parse teks koordinat yang disalin dari Pixel Ruler. "
            "Titik: '(x, y)'. Area: '(x1=.., y1=..) (x2=.., y2=..) ukuran=WxHpx'. "
            "Mengembalikan objek terstruktur, atau error parsing."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Teks koordinat mentah dari clipboard.",
                },
                "image_width": {
                    "type": "integer",
                    "description": "Lebar gambar (opsional) untuk validasi batas.",
                },
                "image_height": {
                    "type": "integer",
                    "description": "Tinggi gambar (opsional) untuk validasi batas.",
                },
            },
            "required": ["text"],
        },
    },
    {
        "name": "interpret_area",
        "description": (
            "Hitung interpretasi area dari teks seleksi Pixel Ruler: "
            "span, luas piksel (w+1)x(h+1), koordinat tengah."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Teks seleksi area, mis. '(x1=10, y1=20) (x2=39, y2=49) ukuran=29x29px'.",
                }
            },
            "required": ["text"],
        },
    },
]


def tools_call(name, args):
    if name == "parse_coordinates":
        text = args.get("text", "")
        point = parse_point(text)
        area = parse_area(text)
        parsed = point or area
        if parsed is None:
            return {
                "ok": False,
                "error": (
                    "Format tidak dikenali. Gunakan titik '(x, y)' atau "
                    "area '(x1=.., y1=..) (x2=.., y2=..) ukuran=WxHpx'."
                ),
            }
        if "error" in parsed:
            return {"ok": False, "error": parsed["error"], "data": parsed}
        result = {"ok": True, "data": parsed}
        iw, ih = args.get("image_width"), args.get("image_height")
        if iw is not None and ih is not None:
            if parsed["x"] if parsed["kind"] == "point" else parsed["x2"] >= iw:
                result["warning"] = "x melewati batas gambar (width={})".format(iw)
            if parsed["y"] if parsed["kind"] == "point" else parsed["y2"] >= ih:
                result["warning"] = "y melewati batas gambar (height={})".format(ih)
        return result
    if name == "interpret_area":
        text = args.get("text", "")
        area = parse_area(text)
        if area is None or "error" in area:
            return {
                "ok": False,
                "error": "Format area tidak valid atau tidak dikenali.",
            }
        return {
            "ok": True,
            "data": {
                "kind": "area",
                "x1": area["x1"], "y1": area["y1"],
                "x2": area["x2"], "y2": area["y2"],
                "span": area["span"],
                "span_width_px": area["width"],
                "span_height_px": area["height"],
                "pixel_columns": area["width"] + 1,
                "pixel_rows": area["height"] + 1,
                "pixel_count": area["pixel_count"],
                "center": area["center"],
            },
        }
    return {"ok": False, "error": "Tool tidak dikenal: {}".format(name)}


def text_result(message):
    return {
        "content": [{"type": "text", "text": json.dumps(message, indent=2)}],
    }


def handle(msg):
    m = msg.get("method")
    mid = msg.get("id")
    if m == "initialize":
        return {
            "jsonrpc": "2.0", "id": mid,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        }
    if m == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if m == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}}
    if m == "tools/call":
        params = msg.get("params", {})
        name = params.get("name")
        args = params.get("arguments", {}) or {}
        try:
            result = tools_call(name, args)
        except Exception as e:  # noqa: BLE001
            return {
                "jsonrpc": "2.0", "id": mid,
                "result": {
                    "content": [{"type": "text", "text": "Error: {}".format(e)}],
                    "isError": True,
                },
            }
        return {"jsonrpc": "2.0", "id": mid, "result": text_result(result)}
    return {"jsonrpc": "2.0", "id": mid, "result": {"content": []}}


def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if msg.get("method") == "notifications/initialized":
            continue
        resp = handle(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()