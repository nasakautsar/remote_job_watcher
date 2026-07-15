# fetcher.py
# Tugasnya cuma mengambil data mentah dari sebuah URL -- entah bentuknya
# HTML atau JSON.
#
# File ini SENGAJA tidak tahu:
# - BeautifulSoup / parsing HTML
# - CSV / pandas
# - apa itu "job" atau struktur datanya
#
# fetch_page()  -> HTML (string)
# fetch_json()  -> JSON (Python object: list/dict)
#
# Keduanya berbagi logic retry/timeout/headers/error-handling yang sama
# persis, cuma beda di baris terakhir (response.text vs response.json()).
# Makanya logic itu ditarik ke _request_with_retry() supaya tidak
# copy-paste dua kali -- ini yang membedakan fetch_page() dari fetch_json()
# cuma satu baris, sisanya reuse.

import time
import requests

from config import HEADERS, TIMEOUT, MAX_RETRIES


def _request_with_retry(url):
    """
    Lakukan request ke url dengan retry/timeout/error-handling.
    Return: objek response kalau berhasil, None kalau gagal setelah semua retry.
    Dipakai bareng oleh fetch_page() dan fetch_json() -- keduanya cuma beda
    di bagaimana mereka membaca response ini.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()
            return response

        except requests.exceptions.Timeout:
            print(f"  [fetcher] Timeout ambil {url} (percobaan {attempt}/{MAX_RETRIES})")
            wait = 1

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else None

            if status == 429:
                # Rate limited. Hormati header Retry-After kalau server
                # kasih tahu berapa lama harus nunggu; kalau tidak ada,
                # exponential backoff (5s, 10s, 20s, ...) -- kalau rate
                # limit-nya karena akumulasi banyak request dalam window
                # waktu tertentu (bukan cuma 1x kena), flat 5s tiap
                # percobaan kemungkinan besar tidak akan pernah cukup.
                retry_after = e.response.headers.get("Retry-After") if e.response is not None else None
                if retry_after and retry_after.isdigit():
                    wait = int(retry_after)
                else:
                    wait = 5 * (2 ** (attempt - 1))
                print(f"  [fetcher] Rate limited (429) di {url}, tunggu {wait}s "
                      f"(percobaan {attempt}/{MAX_RETRIES})")
            else:
                print(f"  [fetcher] HTTP error di {url}: {e} (percobaan {attempt}/{MAX_RETRIES})")
                wait = 1

        except requests.exceptions.RequestException as e:
            print(f"  [fetcher] Gagal ambil {url}: {e} (percobaan {attempt}/{MAX_RETRIES})")
            wait = 1

        if attempt < MAX_RETRIES:
            time.sleep(wait)

    return None


def fetch_page(url):
    """
    Ambil HTML dari url.
    Return: string HTML kalau berhasil, None kalau gagal setelah semua retry.
    """
    response = _request_with_retry(url)
    return response.text if response else None


def fetch_json(url):
    """
    Ambil JSON dari url, langsung di-parse jadi Python object (list/dict).
    Return: Python object kalau berhasil, None kalau gagal setelah semua
    retry ATAU kalau body response ternyata bukan JSON valid.
    """
    response = _request_with_retry(url)
    if response is None:
        return None

    try:
        return response.json()
    except ValueError as e:
        print(f"  [fetcher] Gagal parse JSON dari {url}: {e}")
        return None