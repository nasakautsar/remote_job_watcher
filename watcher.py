# watcher.py
# Ini "conductor". Tidak mengerjakan fetch/parse/save sendiri --
# cuma mengatur urutan siapa mengerjakan apa, lalu kapan.
#
# Flow: Fetch -> Parse -> Merge -> Export -> Summary

from config import SOURCES, OUTPUT_PATH, DELAY_BETWEEN_SOURCES, DELAY_SAME_DOMAIN
from fetcher import fetch_page, fetch_json
from parser import parse_jobs
from exporter import save_csv
from urllib.parse import urlparse
import time


def _domain(url):
    return urlparse(url).netloc


def run():
    all_jobs = []  # ini tempat "Merge" terjadi: gabungan hasil dari semua source

    source_names = list(SOURCES.items())
    for i, (name, source) in enumerate(source_names):
        url = source["url"]
        source_type = source["type"]

        print(f"[watcher] Fetch: {name} ({url}) [{source_type}]")

        # Watcher cuma memilih fetch_json() vs fetch_page() berdasarkan
        # type. Setelah itu watcher tidak peduli lagi apakah datanya
        # tadinya HTML atau JSON -- parse_jobs() yang urus itu, dan
        # keduanya sama-sama pulang sebagai list of dict.
        if source_type == "api":
            raw = fetch_json(url)
        else:
            raw = fetch_page(url)

        if raw is None:
            print(f"[watcher] Gagal fetch {name}, sumber ini dilewati.")
            continue

        print(f"[watcher] Parse: {name}")
        jobs = parse_jobs(raw, name)
        print(f"[watcher]   -> {len(jobs)} item ditemukan")

        all_jobs.extend(jobs)  # Merge

        # Jeda sebelum lanjut ke source berikutnya. Kalau source berikutnya
        # domainnya SAMA dengan yang barusan (misal HN -> HN Jobs), kasih
        # jeda lebih lama -- domain yang sama dalam waktu berdekatan lebih
        # rawan kena rate limit. Ini cuma mitigasi, bukan jaminan -- kalau
        # rate limit-nya karena akumulasi request dari banyak run
        # sebelumnya (bukan cuma dalam 1x run ini), delay di sini tidak
        # akan menolong; solusinya cuma nunggu di luar script.
        if i < len(source_names) - 1:
            next_url = source_names[i + 1][1]["url"]
            if _domain(next_url) == _domain(url):
                time.sleep(DELAY_SAME_DOMAIN)
            else:
                time.sleep(DELAY_BETWEEN_SOURCES)

    print(f"[watcher] Export: total {len(all_jobs)} item ke {OUTPUT_PATH}")
    saved = save_csv(all_jobs, OUTPUT_PATH)

    if saved:
        print("Export completed.")
    else:
        print("Nothing exported.")

    _print_summary(all_jobs)


def _print_summary(all_jobs):
    print("\n=== Summary ===")
    print(f"Sources difetch : {len(SOURCES)} ({', '.join(SOURCES.keys())})")
    print(f"Total item       : {len(all_jobs)}")
    if not all_jobs:
        print("Peringatan: 0 item ditemukan. Kemungkinan selector di parser.py")
        print("perlu disesuaikan, atau situsnya memblokir request (lihat")
        print("catatan di bagian atas parser.py).")


if __name__ == "__main__":
    run()