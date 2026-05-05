# 🤖 Universal Telegram Downloader Bot

YouTube, Instagram, Pinterest, Facebook ve 1000+ siteden video, müzik ve fotoğraf indiren Telegram botu.

---

## ✅ Desteklenen Siteler & Formatlar

| Platform     | Video | Müzik (MP3) | Fotoğraf |
|-------------|-------|-------------|----------|
| YouTube     | ✅    | ✅           | ✅        |
| Instagram   | ✅    | ✅           | ✅        |
| Pinterest   | ✅    | -            | ✅        |
| Facebook    | ✅    | ✅           | ✅        |
| Twitter/X   | ✅    | ✅           | ✅        |
| TikTok      | ✅    | ✅           | ✅        |
| Vimeo       | ✅    | ✅           | ✅        |
| SoundCloud  | -     | ✅           | -         |
| Reddit      | ✅    | ✅           | ✅        |
| Dailymotion | ✅    | ✅           | ✅        |
| Twitch      | ✅    | -            | -         |
| +1000 site  | ✅    | ✅           | ✅        |

### 🎬 Video Kaliteleri
`360p` · `480p` · `720p` · `1080p` · `1440p` · `2K (2048p)`

### 🎵 Müzik
Sadece **MP3** — 320kbps (en yüksek kalite)

### 🖼 Fotoğraf
Orijinal / 1080p kalite

---

## 🚀 Kurulum

### 1. Gereksinimler
- Python 3.11+
- ffmpeg (video/ses dönüşümü için **zorunlu**)

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install -y ffmpeg

# macOS
brew install ffmpeg

# Windows
# https://ffmpeg.org/download.html adresinden indirin
# PATH'e ekleyin
```

### 2. Botu indirin
```bash
git clone <repo_url>
cd telegram_downloader_bot
```

### 3. Sanal ortam & bağımlılıklar
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Bot token'ı ayarlayın

**@BotFather**'a gidin → `/newbot` → token alın.

```bash
cp .env.example .env
# .env dosyasını açın ve BOT_TOKEN satırını düzenleyin
```

Ya da doğrudan `bot.py` içinde:
```python
BOT_TOKEN = "1234567890:AAF..."
```

### 5. Botu başlatın
```bash
# .env kullanarak
export $(cat .env | xargs)
python bot.py

# Ya da direkt
BOT_TOKEN="TOKEN_HERE" python bot.py
```

---

## 📁 Dosya Yapısı

```
telegram_downloader_bot/
├── bot.py           # Ana bot mantığı
├── downloader.py    # yt-dlp indirici modülü
├── requirements.txt # Python bağımlılıkları
├── .env.example     # Örnek konfigürasyon
├── downloads/       # Geçici indirme klasörü (otomatik silinir)
└── README.md
```

---

## ⚙️ Nasıl Çalışır?

```
Kullanıcı link gönderir
        ↓
Bot linki tanır (platform tespiti)
        ↓
Format seçimi: Video / Müzik / Fotoğraf
        ↓
Video ise kalite seçimi: 360p → 2K
        ↓
yt-dlp ile indirir + ffmpeg ile dönüştürür
        ↓
Telegram'a gönderir + geçici dosyayı siler
```

---

## ⚠️ Önemli Notlar

- **Telegram Bot API limiti:** 50 MB (dosya gönderme)
  - Büyük videolar için [Local Bot API Server](https://core.telegram.org/bots/api#using-a-local-bot-api-server) kurabilirsiniz (2 GB'a kadar)
- **Özel/gizli içerik:** Instagram/Facebook özel hesap içerikleri indirilemez
- **Telif hakkı:** Yalnızca kişisel kullanım için indirin
- **Cookies:** YouTube/Instagram oturumu gerekiyorsa `cookies.txt` desteği eklenebilir

---

## 🔧 Gelişmiş: Cookies Desteği (YouTube Login)

`downloader.py` içinde ydl_opts'a ekleyin:
```python
"cookiefile": "/path/to/cookies.txt",
```
Tarayıcıdan cookie almak için: [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)

---

## 🐳 Docker ile Çalıştırma (Opsiyonel)

```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y ffmpeg
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

```bash
docker build -t dl-bot .
docker run -e BOT_TOKEN="TOKEN_HERE" dl-bot
```
