import os
import re
import uuid
import logging
import requests
from pathlib import Path
from urllib.parse import urlparse

try:
    import yt_dlp
except ImportError:
    raise RuntimeError("yt-dlp kurulu değil: pip install yt-dlp")

logger = logging.getLogger(__name__)

# Max file sizes for Telegram (in bytes)
MAX_VIDEO_SIZE = 2_000_000_000   # ~2 GB (Bot API limit 50MB, local server: 2GB)
MAX_AUDIO_SIZE =   500_000_000   # 500 MB
MAX_PHOTO_SIZE =    50_000_000   #  50 MB

QUALITY_FORMAT_MAP = {
    360:  "bestvideo[height<=360]+bestaudio/best[height<=360]/best",
    480:  "bestvideo[height<=480]+bestaudio/best[height<=480]/best",
    720:  "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
    1080: "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
    1440: "bestvideo[height<=1440]+bestaudio/best[height<=1440]/best",
    2048: "bestvideo[height<=2048]+bestaudio/best[height<=2048]/best",
}

class Downloader:
    def __init__(self, download_dir: str):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    # ── Public entry point ────────────────────────────────────────────────
    def download(self, url: str, media_type: str, quality: int | None) -> tuple[str, str]:
        """
        Returns (file_path, title).
        Raises on failure.
        """
        if media_type == "video":
            return self._download_video(url, quality or 720)
        elif media_type == "audio":
            return self._download_audio(url)
        elif media_type == "photo":
            return self._download_photo(url)
        else:
            raise ValueError(f"Bilinmeyen medya türü: {media_type}")

    # ── Video ─────────────────────────────────────────────────────────────
    def _download_video(self, url: str, quality: int) -> tuple[str, str]:
        uid = uuid.uuid4().hex[:8]
        out_tmpl = str(self.download_dir / f"video_{uid}.%(ext)s")
        fmt = QUALITY_FORMAT_MAP.get(quality, QUALITY_FORMAT_MAP[720])

        ydl_opts = {
            "format": fmt,
            "outtmpl": out_tmpl,
            "merge_output_format": "mp4",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4",
                }
            ],
        }

        title = self._run_ydl(url, ydl_opts, uid, "video")
        file_path = self._find_file(uid, "video")
        self._check_size(file_path, MAX_VIDEO_SIZE, "Video")
        return str(file_path), title

    # ── Audio ─────────────────────────────────────────────────────────────
    def _download_audio(self, url: str) -> tuple[str, str]:
        uid = uuid.uuid4().hex[:8]
        out_tmpl = str(self.download_dir / f"audio_{uid}.%(ext)s")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": out_tmpl,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }
            ],
        }

        title = self._run_ydl(url, ydl_opts, uid, "audio")
        file_path = self._find_file(uid, "audio")
        self._check_size(file_path, MAX_AUDIO_SIZE, "Müzik")
        return str(file_path), title

    # ── Photo ─────────────────────────────────────────────────────────────
    def _download_photo(self, url: str) -> tuple[str, str]:
        """
        Pinterest, Instagram, Facebook gibi sitelerden fotoğraf indirir.
        yt-dlp thumbnail/image extraction + fallback direkt indirme.
        """
        uid = uuid.uuid4().hex[:8]

        # 1. yt-dlp ile dene (Instagram, Pinterest vb.)
        out_tmpl = str(self.download_dir / f"photo_{uid}.%(ext)s")
        ydl_opts = {
            "format": "best",
            "outtmpl": out_tmpl,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "writethumbnail": True,
            "skip_download": True,          # sadece thumbnail al
            "postprocessors": [
                {"key": "FFmpegThumbnailsConvertor", "format": "jpg"}
            ],
        }

        try:
            title = self._run_ydl(url, ydl_opts, uid, "photo")
            file_path = self._find_file(uid, "photo")
            if file_path.exists():
                self._check_size(file_path, MAX_PHOTO_SIZE, "Fotoğraf")
                return str(file_path), title
        except Exception:
            pass

        # 2. Fallback: direkt download ile dene (Pinterest pin, direct image URL)
        try:
            file_path, title = self._direct_image_download(url, uid)
            self._check_size(file_path, MAX_PHOTO_SIZE, "Fotoğraf")
            return str(file_path), title
        except Exception:
            pass

        # 3. yt-dlp ile video olarak indir, thumbnail çıkar
        out_tmpl2 = str(self.download_dir / f"photo_{uid}_v.%(ext)s")
        ydl_opts2 = {
            "format": "best",
            "outtmpl": out_tmpl2,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts2) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "photo")
            thumb = info.get("thumbnail")

        if thumb:
            img_path = self.download_dir / f"photo_{uid}.jpg"
            r = requests.get(thumb, timeout=30)
            r.raise_for_status()
            img_path.write_bytes(r.content)
            return str(img_path), title

        raise RuntimeError("Bu linkten fotoğraf indirilemedi.")

    # ── Helpers ───────────────────────────────────────────────────────────
    def _run_ydl(self, url: str, opts: dict, uid: str, kind: str) -> str:
        """Runs yt-dlp and returns the video title."""
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return info.get("title") or info.get("id") or kind

    def _find_file(self, uid: str, kind: str) -> Path:
        """Finds the downloaded file by uid prefix."""
        candidates = list(self.download_dir.glob(f"{kind}_{uid}*"))
        if not candidates:
            raise FileNotFoundError(f"İndirilen dosya bulunamadı: {kind}_{uid}*")
        # Prefer mp4/mp3/jpg
        for ext in (".mp4", ".mp3", ".jpg", ".jpeg", ".png", ".webp", ".m4a"):
            for c in candidates:
                if c.suffix.lower() == ext:
                    return c
        return candidates[0]

    def _check_size(self, path: Path, max_bytes: int, label: str):
        size = path.stat().st_size
        mb = size / 1_000_000
        max_mb = max_bytes / 1_000_000
        if size > max_bytes:
            path.unlink(missing_ok=True)
            raise RuntimeError(
                f"{label} çok büyük ({mb:.0f} MB). "
                f"Maksimum: {max_mb:.0f} MB. "
                "Daha düşük kalite deneyin."
            )

    def _direct_image_download(self, url: str, uid: str) -> tuple[Path, str]:
        """Direct HTTP download for plain image URLs."""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        }
        r = requests.get(url, headers=headers, timeout=30, stream=True)
        r.raise_for_status()
        ct = r.headers.get("content-type", "")
        if not ct.startswith("image/"):
            raise ValueError(f"İçerik türü görsel değil: {ct}")
        ext = ct.split("/")[-1].split(";")[0] or "jpg"
        path = self.download_dir / f"photo_{uid}.{ext}"
        with open(path, "wb") as f:
            for chunk in r.iter_content(1024 * 64):
                f.write(chunk)
        parsed = urlparse(url)
        title = Path(parsed.path).stem or "image"
        return path, title
