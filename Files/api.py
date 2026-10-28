from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
import os
import json
from bs4 import BeautifulSoup
import yt_dlp
from user_agent import generate_user_agent

app = Flask(__name__)
CORS(app)

DEVELOPER = "t.me/KingXRomeo"
CHANNEL = "@RomeoXOfficial"
OWNER = "@KingXRomeo"

COOKIES_PATH = "cookies.txt"


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


# ============================================================
# FACEBOOK (Working - No Change)
# ============================================================
def get_fb_video(url):
    headers = {
        'User-Agent': generate_user_agent(),
        'Origin': 'https://fbdown.blog',
        'Referer': 'https://fbdown.blog/',
    }
    try:
        r = requests.post('https://fbdown.blog/get.php', headers=headers, data={'url': url}, timeout=15)
        data = r.json()['data']
        title = data.get("title", "Unknown Title")
        author = data.get("author", "Unknown Author")
        duration_sec = data.get("duration", 0)
        thumbnail = data.get("thumbnail", "")
        mins = int(duration_sec // 60)
        secs = int(duration_sec % 60)
        duration_str = f"{mins:02d}:{secs:02d}"
        hd = sd = "Not available"
        for m in data.get("medias", []):
            if m.get("quality") == "HD":
                hd = m["url"]
            elif m.get("quality") == "SD" and sd == "Not available":
                sd = m["url"]
        return {
            "status": "success",
            "video": {"title": title, "author": author, "duration": duration_str,
                      "thumbnail": thumbnail, "hd": hd, "sd": sd},
            "Developer": DEVELOPER, "Main Channel": CHANNEL, "Owner": OWNER
        }
    except:
        return {"status": "error", "message": "Facebook video not found",
                "Developer": DEVELOPER, "Main Channel": CHANNEL, "Owner": OWNER}


# ============================================================
# INSTAGRAM (Working - No Change)
# ============================================================
def download_insta_reel(url):
    try:
        ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True, "format": "best"}
        if os.path.exists(COOKIES_PATH):
            ydl_opts["cookiefile"] = COOKIES_PATH
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info.get('url')
            if not video_url and info.get('formats'):
                video_url = info['formats'][-1].get('url')
            if video_url:
                return {"status": "success", "video": video_url,
                        "title": info.get('title', 'Instagram Video'),
                        "Developer": DEVELOPER, "Main Channel": CHANNEL, "Owner": OWNER}
    except:
        pass

    try:
        session = requests.Session()
        ua = generate_user_agent()
        session.get('https://snapdownloader.com/tools/instagram-reels-downloader/download',
                    headers={'User-Agent': ua}, timeout=15)
        r = session.post('https://grabgram.io/api/fetch/instagram',
                         headers={'User-Agent': ua, 'Content-Type': 'application/json',
                                  'Origin': 'https://grabgram.io', 'Referer': 'https://grabgram.io/'},
                         json={'url': url.strip(), 'tool': 'reels'}, timeout=20)
        if r.status_code == 200:
            data = r.json()
            if data.get('ok') and data.get('data', {}).get('items'):
                for item in data['data']['items']:
                    downloads = item.get('downloads', [])
                    if downloads:
                        return {"status": "success", "video": downloads[0].get('url'),
                                "title": data['data'].get('caption', 'Instagram Video'),
                                "Developer": DEVELOPER, "Main Channel": CHANNEL, "Owner": OWNER}
    except:
        pass

    return {"status": "error", "message": "Instagram video not found.",
            "Developer": DEVELOPER, "Main Channel": CHANNEL, "Owner": OWNER}


# ============================================================
# SNAPCHAT (Fixed - Multi-Method)
# ============================================================
def download_snapchat(url):
    # Method 1: Extract from Snapchat page HTML
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        r = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
        html = r.text

        # Pattern 1: snapList with mediaUrl (Spotlight videos)
        match = re.search(r'"snapList":\s*\[\s*\{[^}]*"mediaUrl":\s*"([^"]+)"', html)
        if match:
            video_url = match.group(1).replace('\\u0026', '&').replace('\\/', '/')
            if video_url.startswith('http'):
                title_match = re.search(r'"title":\s*"([^"]+)"', html)
                title = title_match.group(1) if title_match else "Snapchat Video"
                return {"status": "success", "video": video_url, "title": title,
                        "Developer": DEVELOPER, "Main Channel": CHANNEL, "Owner": OWNER}

        # Pattern 2: videoUrl
        match = re.search(r'"videoUrl":\s*"([^"]+)"', html)
        if match:
            video_url = match.group(1).replace('\\u0026', '&').replace('\\/', '/')
            if video_url.startswith('http'):
                return {"status": "success", "video": video_url, "title": "Snapchat Video",
                        "Developer": DEVELOPER, "Main Channel": CHANNEL, "Owner": OWNER}

        # Pattern 3: contentUrl
        match = re.search(r'"contentUrl":\s*"([^"]+)"', html)
        if match:
            video_url = match.group(1).replace('\\u0026', '&').replace('\\/', '/')
            if video_url.startswith('http'):
                return {"status": "success", "video": video_url, "title": "Snapchat Video",
                        "Developer": DEVELOPER, "Main Channel": CHANNEL, "Owner": OWNER}

        # Pattern 4: og:video meta tag
        match = re.search(r'<meta[^>]+property=["\']og:video["\'][^>]+content=["\'](https?://[^"\']+)["\']', html)
        if match:
            video_url = match.group(1).replace('&amp;', '&')
            return {"status": "success", "video": video_url, "title": "Snapchat Video",
                    "Developer": DEVELOPER, "Main Channel": CHANNEL, "Owner": OWNER}

        # Pattern 5: Any direct .mp4 link
        matches = re.findall(r'(https?://[^"\']*\.mp4[^"\']*)', html)
        for m in matches:
            video_url = m.replace('\\u0026', '&').replace('\\/', '/').replace('&amp;', '&')
            if video_url.startswith('http'):
                return {"status": "success", "video": video_url, "title": "Snapchat Video",
                        "Developer": DEVELOPER, "Main Channel": CHANNEL, "Owner": OWNER}

        # Pattern 6: JSON script tag
        match = re.search(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', html, re.DOTALL)
        if match:
            json_text = match.group(1)
            mp4_matches = re.findall(r'(https?:\\?/\\?/[^"\\]*\.mp4[^"\\]*)', json_text)
            for m in mp4_matches:
                video_url = m.replace('\\u0026', '&').replace('\\/', '/').replace('&amp;', '&')
                if video_url.startswith('http'):
                    return {"status": "success", "video": video_url, "title": "Snapchat Video",
                            "Developer": DEVELOPER, "Main Channel": CHANNEL, "Owner": OWNER}
    except Exception as e:
        print(f"Snapchat method 1 error: {e}")

    # Method 2: yt-dlp fallback
    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "format": "best",
        }
        if os.path.exists(COOKIES_PATH):
            ydl_opts["cookiefile"] = COOKIES_PATH
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info.get('url')
            if not video_url and info.get('formats'):
                video_url = info['formats'][-1].get('url')
            if video_url:
                return {"status": "success", "video": video_url,
                        "title": info.get('title', 'Snapchat Video'),
                        "Developer": DEVELOPER, "Main Channel": CHANNEL, "Owner": OWNER}
    except Exception as e:
        print(f"Snapchat method 2 error: {e}")

    return {"status": "error", "message": "Snapchat video not found. Try another link.",
            "Developer": DEVELOPER, "Main Channel": CHANNEL, "Owner": OWNER}


# ============================================================
# PINTEREST (Working - No Change)
# ============================================================
def get_pinterest_download_links(url):
    try:
        headers = {'User-Agent': generate_user_agent()}
        r = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        html = r.text
        for pattern in [r'"video_url":"(https?://[^"]+)"',
                        r'<meta[^>]+property="og:video"[^>]+content="(https?://[^"]+)"',
                        r'"(https?://i\.pinimg\.com/[^"]+\.(?:jpg|png|jpeg|webp))"']:
            matches = re.findall(pattern, html)
            for m in matches:
                if m and ('mp4' in m or 'pinimg' in m):
                    clean_url = m.replace('\\u0026', '&').replace('\\/', '/')
                    clean_url = clean_url.replace('/236x/', '/originals/').replace('/474x/', '/originals/')
                    clean_url = clean_url.replace('/564x/', '/originals/').replace('/736x/', '/originals/')
                    clean_url = clean_url.replace('/1200x/', '/originals/')
                    if 'mp4' in clean_url:
                        return {"status": "success", "video": clean_url, "title": 'Pinterest Video',
                                "Developer": DEVELOPER, "Main Channel": CHANNEL, "Owner": OWNER}
                    else:
                        return {"status": "success", "photo": clean_url, "title": 'Pinterest Image',
                                "Developer": DEVELOPER, "Main Channel": CHANNEL, "Owner": OWNER}
    except:
        pass
    return {"status": "error", "message": "Pinterest media not found. Try another link.",
            "Developer": DEVELOPER, "Main Channel": CHANNEL, "Owner": OWNER}


# ============================================================
# YOUTUBE (Optimized from yt.py - Multi-Client Method)
# ============================================================
def download_youtube(url):
    try:
        if not url:
            return {"status": "error", "message": "YouTube URL is required",
                    "Developer": DEVELOPER, "Main Channel": CHANNEL, "Owner": OWNER}

        # ---------- ATTEMPT 1: Multiple clients (from yt.py approach) ----------
        clients_to_try = [
            ["android_vr"],
            ["ios"],
            ["android"],
            ["mweb"],
            ["tv_embedded"],
            ["web_embedded"],
            ["android", "ios"],
        ]

        last_error = ""

        for client_list in clients_to_try:
            try:
                ydl_opts = {
                    "quiet": True,
                    "no_warnings": True,
                    "skip_download": True,
                    "noplaylist": True,
                    # yt.py's format selection for best quality
                    "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    # yt.py's extractor args
                    "extractor_args": {
                        "youtube": {
                            "player_client": client_list,
                            "player_skip": ["webpage", "configs"],
                        }
                    },
                    # yt.py's speed optimizations
                    "concurrent_fragment_downloads": 16,
                    "retries": 20,
                    "fragment_retries": 20,
                    "socket_timeout": 30,
                    "buffersize": 1024 * 1024,
                    "http_chunk_size": 10 * 1024 * 1024,
                    "geo_bypass": True,
                    "nocheckcertificate": True,
                    "age_limit": 99,
                }

                if os.path.exists(COOKIES_PATH):
                    ydl_opts["cookiefile"] = COOKIES_PATH

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                formats = []
                seen = set()
                for f in info.get("formats", []):
                    u = f.get("url")
                    if not u or u in seen or f.get("vcodec") == "none":
                        continue
                    seen.add(u)
                    formats.append({
                        "quality": f.get("format_note") or f.get("resolution") or "Original",
                        "ext": f.get("ext") or "mp4",
                        "url": u
                    })

                if formats:
                    return {
                        "status": "success",
                        "title": info.get("title", "YouTube Video"),
                        "author": info.get("uploader", "Unknown"),
                        "duration": info.get("duration"),
                        "thumbnail": info.get("thumbnail"),
                        "video": formats,
                        "Developer": DEVELOPER, "Main Channel": CHANNEL, "Owner": OWNER
                    }
            except Exception as e:
                last_error = str(e)[:150]
                print(f"Client {client_list} failed: {last_error}")
                continue

        # ---------- ATTEMPT 2: Invidious public API fallback ----------
        try:
            video_id_match = re.search(r'(?:v=|youtu\.be/|shorts/|embed/)([A-Za-z0-9_-]{11})', url)
            if video_id_match:
                video_id = video_id_match.group(1)
                invidious_instances = [
                    "https://inv.nadeko.net",
                    "https://invidious.nerdvpn.de",
                    "https://yewtu.be",
                    "https://invidious.f5.si",
                    "https://iv.melmac.space",
                    "https://invidious.privacyredirect.com",
                ]
                for instance in invidious_instances:
                    try:
                        api_url = f"{instance}/api/v1/videos/{video_id}"
                        r = requests.get(api_url, timeout=10)
                        if r.status_code == 200:
                            data = r.json()
                            formats = []
                            for f in data.get("formatStreams", []):
                                if f.get("url"):
                                    formats.append({
                                        "quality": f.get("resolution", "Unknown"),
                                        "ext": f.get("container", "mp4"),
                                        "url": f.get("url")
                                    })
                            for f in data.get("adaptiveFormats", []):
                                if f.get("url") and "video" in f.get("type", ""):
                                    formats.append({
                                        "quality": f.get("qualityLabel", "Unknown"),
                                        "ext": "mp4",
                                        "url": f.get("url")
                                    })
                            if formats:
                                return {
                                    "status": "success",
                                    "title": data.get("title", "YouTube Video"),
                                    "author": data.get("author", "Unknown"),
                                    "duration": data.get("lengthSeconds"),
                                    "thumbnail": data.get("videoThumbnails", [{}])[0].get("url", ""),
                                    "video": formats,
                                    "Developer": DEVELOPER, "Main Channel": CHANNEL, "Owner": OWNER
                                }
                    except:
                        continue
        except:
            pass

        return {"status": "error",
                "message": f"YouTube ने इस वीडियो को block किया। दूसरी वीडियो try करें। ({last_error[:80]})",
                "Developer": DEVELOPER, "Main Channel": CHANNEL, "Owner": OWNER}

    except Exception as e:
        return {"status": "error", "message": f"YouTube failed: {str(e)}",
                "Developer": DEVELOPER, "Main Channel": CHANNEL, "Owner": OWNER}


# ============================================================
# ROUTES
# ============================================================
@app.route('/', methods=['GET'])
def index():
    return jsonify({"Developer": DEVELOPER, "Status": "Running",
                    "Main Channel": CHANNEL, "Owner": OWNER})


@app.route('/facebook', methods=['GET', 'POST'])
def fb():
    return jsonify(get_fb_video(request.values.get("video", "").strip()))


@app.route('/Instagram', methods=['GET', 'POST'])
def insta():
    return jsonify(download_insta_reel(request.values.get("video", "").strip()))


@app.route('/snap', methods=['GET', 'POST'])
def snap():
    return jsonify(download_snapchat(request.values.get("video", "").strip()))


@app.route('/Pinterest', methods=['GET', 'POST'])
def pin():
    return jsonify(get_pinterest_download_links(request.values.get("video", "").strip()))


@app.route('/youtube', methods=['GET', 'POST'])
def youtube():
    return jsonify(download_youtube(request.values.get("video", "").strip()))


app = app