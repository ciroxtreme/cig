#!/usr/bin/env python3
"""Kirim hasil download yt-dlp ke Telegram.
Dibaca dari folder out/. Kalau kosong/gagal, kirim pesan gagal.
Env: BOT_TOKEN, CHAT_ID, URL. YTDLP_FAILED=1 kalau yt-dlp gagal.
"""
import json
import os
import urllib.request

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
URL = os.environ.get("URL", "")
FAILED = os.environ.get("YTDLP_FAILED") == "1"
API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def tg(method, payload, files=None):
    if files:
        import uuid
        boundary = "----tg" + uuid.uuid4().hex
        body = b""
        for k, v in payload.items():
            body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
        for name, (fname, data, ctype) in files.items():
            body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"; filename=\"{fname}\"\r\nContent-Type: {ctype}\r\n\r\n".encode() + data + b"\r\n"
        body += f"--{boundary}--\r\n".encode()
        req = urllib.request.Request(
            f"{API}/{method}", data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
    else:
        req = urllib.request.Request(
            f"{API}/{method}",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def send_text(text):
    tg("sendMessage", {"chat_id": CHAT_ID, "text": text})


def main():
    files = []
    if os.path.isdir("out"):
        for f in sorted(os.listdir("out")):
            p = os.path.join("out", f)
            if os.path.isfile(p) and os.path.getsize(p) > 0:
                files.append(p)
    if not files:
        reason = "yt-dlp gagal download." if FAILED else "tidak ada media yang ke-download."
        send_text(f"❌ Gagal download Instagram.\n{reason}\nLink: {URL}")
        return
    for p in files:
        name = os.path.basename(p)
        data = open(p, "rb").read()
        ext = os.path.splitext(name)[1].lower()
        try:
            if ext == ".mp4":
                tg("sendVideo", {"chat_id": CHAT_ID, "caption": f"📸 {URL}"},
                   files={"video": (name, data, "video/mp4")})
            elif ext in (".jpg", ".jpeg", ".png", ".webp"):
                ctype = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
                tg("sendPhoto", {"chat_id": CHAT_ID, "caption": f"📸 {URL}"},
                   files={"photo": (name, data, ctype)})
            else:
                tg("sendDocument", {"chat_id": CHAT_ID, "caption": f"📸 {URL}"},
                   files={"document": (name, data, "application/octet-stream")})
        except Exception as e:
            send_text(f"❌ Gagal kirim file {name}: {e}")


if __name__ == "__main__":
    main()
