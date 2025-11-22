#!/usr/bin/env python3
import argparse
import csv
import io
import re
import requests
import sys
from html import escape
from datetime import timedelta
import ftplib
import json
import os

# ============ BEÁLLÍTÁSOK ============
SHEET_ID = "11QeYYndsbJPYI56PN2GowL10CVYdoiFPDsYoRSc-iJg"
SHEET_GID = "1475185902"  # ezt a böngésző címsorából másold ki!
SHEET_EXPORT_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"

# FTP adatok betöltése config.json-ból
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        cfg = json.load(f)
    FTP_HOST = cfg.get("FTP_HOST")
    FTP_USER = cfg.get("FTP_USER")
    FTP_PASS = cfg.get("FTP_PASS")
    FTP_PATH = cfg.get("FTP_PATH")
else:
    FTP_HOST = FTP_USER = FTP_PASS = FTP_PATH = None

YOUTUBE_API_KEY = "AIzaSyC8YiUWDALdTthO3nBiHosKbGymNKpyL7M"  # vagy hagyd üresen, ha nem kell
# ====================================

YOUTUBE_VIDEO_ID_RE = re.compile(
    r"(?:v=|\/v\/|youtu\.be\/|\/embed\/|\/watch\?v=)([A-Za-z0-9_-]{11})"
)

def extract_youtube_id(url):
    if not url:
        return None
    m = YOUTUBE_VIDEO_ID_RE.search(url)
    if m:
        return m.group(1)
    # sometimes only id is provided
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url.strip()):
        return url.strip()
    return None

def human_readable_duration(iso_duration):
    # ISO 8601 duration like PT1H2M30S
    if not iso_duration:
        return ""
    # simple parser
    hours = minutes = seconds = 0
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_duration)
    if not m:
        return ""
    if m.group(1): hours = int(m.group(1))
    if m.group(2): minutes = int(m.group(2))
    if m.group(3): seconds = int(m.group(3))
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def fetch_csv(url):
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    # ensure correct newline handling
    text = resp.content.decode('utf-8')
    return io.StringIO(text)

def fetch_youtube_metadata(video_ids, api_key):
    """
    video_ids: list of ids (<=50 best)
    returns dict id -> {duration, publishedAt}
    """
    out = {}
    if not api_key:
        return out
    BATCH = 50
    for i in range(0, len(video_ids), BATCH):
        batch = video_ids[i:i+BATCH]
        ids = ",".join(batch)
        url = ("https://www.googleapis.com/youtube/v3/videos"
               "?part=contentDetails,snippet&id={ids}&key={key}").format(ids=ids, key=api_key)
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()
        for item in data.get("items", []):
            vid = item.get("id")
            dur = item.get("contentDetails", {}).get("duration")
            pub = item.get("snippet", {}).get("publishedAt")
            out[vid] = {"duration": dur, "publishedAt": pub}
    return out

def build_html(items, title="Hetiszakasz archívum", placeholder_img=None):
    # items: list of dicts: title, link, thumbnail, duration (opt), publishedAt (opt)
    head = """<!doctype html>
<html lang="hu">
<head>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-GNC4ZCSKY9"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-GNC4ZCSKY9');
</script>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Heti Tóra</title>
<link rel="manifest" href="manifest.json">
<link rel="icon" type="image/png" sizes="192x192" href="icon-192.png">
<link rel="icon" type="image/png" sizes="512x512" href="icon-512.png">
<meta name="description" content="Heti Tóra">
<style>
:root{--gap:12px;--card-radius:12px;--maxw:1100px;}
*{box-sizing:border-box}
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,'Helvetica Neue',Arial;line-height:1.35;margin:16px;background:#f7f7f8;color:#111}
.container{max-width:var(--maxw);margin:0 auto}
.header{display:flex;align-items:center;gap:12px;margin-bottom:12px}
h1{font-size:1.25rem;margin:0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:var(--gap)}
.card{background:#fff;border-radius:var(--card-radius);overflow:hidden;box-shadow:0 6px 18px rgba(20,20,20,0.06);display:flex;flex-direction:column;text-decoration:none;color:inherit}
.thumb{position:relative;aspect-ratio:16/9;background:#ddd}
.thumb img{width:100%;height:100%;object-fit:cover;display:block}
.meta-badge{position:absolute;right:8px;bottom:8px;background:rgba(0,0,0,0.8);color:#fff;padding:4px 6px;border-radius:6px;font-size:0.85rem}
.card-body{padding:10px 12px;display:flex;flex-direction:column;gap:8px;flex:1}
.title{font-weight:600;font-size:0.98rem;margin:0;line-height:1.2}
.sub{font-size:0.85rem;color:#555}
.footer-note{margin-top:12px;font-size:0.85rem;color:#666}
@media (max-width:420px){
  .grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  h1{font-size:1.05rem}
}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Aktuális hetiszakasz archívum – Binjomin rabbitól</h1>
  </div>
  <div class="grid">
"""
    cards = []
    for it in items:
        t = escape(it.get("title",""))
        link = escape(it.get("link",""))
        thumb = escape(it.get("thumbnail") or placeholder_img or "")
        duration = it.get("duration") or ""
        publishedAt = it.get("publishedAt") or ""
        pub_display = ""
        if publishedAt:
            # publishedAt like 2023-01-02T... -> show YYYY-MM-DD
            pub_display = publishedAt.split("T")[0]
        badge = duration or pub_display
        badge_html = f'<div class="meta-badge">{escape(badge)}</div>' if badge else ""
        card = f'''
    <a class="card" href="{link}" target="_blank" rel="noopener noreferrer">
      <div class="thumb">
        <img loading="lazy" src="{thumb}" alt="{t}">
        {badge_html}
      </div>
      <div class="card-body">
        <div class="title">{t}</div>
        <div class="sub">{escape(pub_display)}</div>
      </div>
    </a>
'''
        cards.append(card)
    tail = """
  </div>
  <div class="footer-note" style="text-align:center;margin-top:32px;font-size:9px;">
    Powered by <a href="https://github.com/binyominzeev/weekly-torah" target="_blank" rel="noopener noreferrer" style="color:#444;text-decoration:underline dotted;">Weekly Torah</a>
  </div>
</div>
</body>
</html>
"""
    return head + "".join(cards) + tail

def upload_ftp(host, user, passwd, remote_path, local_file_path):
    # remote_path should be directory or full path; we'll try to change cwd to it, otherwise upload by full path
    ftp = ftplib.FTP(host, timeout=30)
    ftp.login(user, passwd)
    try:
        # try to CWD
        ftp.cwd(remote_path)
        with open(local_file_path, "rb") as f:
            ftp.storbinary(f"STOR {local_file_path.split('/')[-1]}", f)
    except ftplib.error_perm:
        # attempt to store by full path
        with open(local_file_path, "rb") as f:
            ftp.storbinary(f"STOR " + remote_path + local_file_path.split('/')[-1], f)
    ftp.quit()

def main():
    p = argparse.ArgumentParser()
    # p.add_argument("--youtube-api-key", default=None, help="(opcionális) YouTube Data API v3 kulcs")
    p.add_argument("--placeholder-image", default="", help="placeholder thumbnail ha nincs ID")
    args = p.parse_args()

    OUT_FILE = "index.html"
    youtube_api_key = YOUTUBE_API_KEY  # mindig ezt használja

    try:
        csv_stream = fetch_csv(SHEET_EXPORT_URL)
    except Exception as e:
        print("HIBA: Nem sikerült letölteni a Google Sheets CSV-t. Ellenőrizd az URL-t és a megosztási beállításokat.")
        print("Részlet:", e)
        sys.exit(1)

    reader = csv.DictReader(csv_stream)
    rows = list(reader)
    items = []
    video_ids = []
    for r in rows:
        title = r.get("title") or r.get("Title") or ""
        link = r.get("link") or r.get("Link") or ""
        vid = extract_youtube_id(link)
        thumbnail = None
        if vid:
            thumbnail = f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"
            video_ids.append(vid)
        else:
            thumbnail = args.placeholder_image or ""

        items.append({
            "title": title.strip(),
            "link": link.strip(),
            "yt_id": vid,
            "thumbnail": thumbnail
        })

    meta = {}
    if youtube_api_key and video_ids:
        try:
            meta = fetch_youtube_metadata(video_ids, youtube_api_key)
        except Exception as e:
            print("YouTube API lekérés közben hiba:", e)
            meta = {}

    # attach duration/publishedAt where available
    for it in items:
        vid = it.get("yt_id")
        if vid and vid in meta:
            it["duration"] = human_readable_duration(meta[vid].get("duration"))
            it["publishedAt"] = meta[vid].get("publishedAt")

    html = build_html(items, placeholder_img=args.placeholder_image)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Kész: {OUT_FILE}")

    try:
        print("FTP feltöltés megkezdése...")
        upload_ftp(FTP_HOST, FTP_USER, FTP_PASS, FTP_PATH, OUT_FILE)
        print("FTP feltöltés kész.")
    except Exception as e:
        print("FTP feltöltés sikertelen:", e)

if __name__ == "__main__":
    main()

