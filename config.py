# config.py
# Semua konstanta project. Tidak ada logic di sini, cuma nilai.

API_URL = "https://remoteok.com/api"

TIMEOUT = 10          # detik, batas tunggu tiap request
MAX_RETRIES = 3       # jumlah percobaan ulang kalau request gagal
DELAY_BETWEEN_SOURCES = 2  # detik, jeda sebelum fetch source berikutnya
DELAY_SAME_DOMAIN = 8      # detik, jeda lebih lama kalau source berikutnya
                           # domainnya sama dengan yang barusan difetch

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
}

OUTPUT_PATH = "remoteok_jobs.csv"

# Tiap source sekarang punya "url" dan "type".
# type menentukan watcher.py harus panggil fetch_json() atau fetch_page():
#   - "api"  -> fetch_json(), raw yang diterima parser adalah Python object
#   - "html" -> fetch_page(), raw yang diterima parser adalah string HTML
SOURCES = {
    "Remote OK": {
        "url": API_URL,
        "type": "api",
    },
    "HN": {
        "url": "https://news.ycombinator.com/",
        "type": "html",
    },
    "HN Jobs": {
        "url": "https://news.ycombinator.com/jobs",
        "type": "html",
    },
    # Catatan: URL ini asumsi -- belum diverifikasi masih aktif/benar,
    # karena tidak ada akses jaringan untuk cek langsung. Kalau redirect
    # atau 404, sesuaikan dulu URL-nya di sini sebelum curiga ke parser.
    "We Work Remotely": {
        "url": "https://weworkremotely.com/remote-jobs",
        "type": "html",
    },
}