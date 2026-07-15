# exporter.py
# Tugasnya cuma SATU: simpan data ke CSV. Selesai. Tidak lebih.

import pandas as pd


# exporter.py
# Tugasnya cuma SATU: simpan data ke CSV. Selesai. Tidak lebih.

import pandas as pd


def save_csv(data, path):
    """
    Save scraped data to CSV.

    Args:
        data (list[dict]): Parsed jobs.
        path (str): Output CSV path.

    Returns:
        bool: True if exported, False otherwise.
    """
    if not data:
        print("[exporter] Tidak ada data untuk disimpan, skip.")
        return False

    df = pd.DataFrame(data)
    # utf-8-sig dipakai (bukan utf-8 biasa) supaya karakter Unicode tampil
    # aman kalau file ini dibuka lewat Excel di Windows -- kasus umum
    # untuk file CSV hasil scraping yang mau dibagikan/dibuka orang lain.
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"[exporter] {len(df)} baris disimpan ke {path}")
    return True