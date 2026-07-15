# parser.py
# Semua selector/mapping spesifik per-source ada di sini.
#
# Dispatcher parse_jobs() menerima `raw` yang bentuknya bisa BEDA
# tergantung source:
#   - kalau source type-nya "html"  -> raw adalah string HTML (dari fetch_page)
#   - kalau source type-nya "api"   -> raw adalah Python object (dari fetch_json)
# Watcher yang menentukan mana yang dipanggil (lihat config.SOURCES / watcher.py).
# parser.py sendiri tidak peduli soal fetching, cuma peduli soal "raw ini
# bentuknya apa, dan gimana cara ubah jadi internal model".

from bs4 import BeautifulSoup

from utils import format_salary


def parse_jobs(raw, source_name):
    """
    Dispatcher: pilih fungsi parsing yang sesuai berdasarkan nama source
    (key di config.SOURCES), karena tiap situs punya struktur data beda.
    """
    if source_name == "Remote OK":
        return _parse_remoteok(raw, source_name)
    elif source_name in ("HN", "HN Jobs"):
        # HN Jobs (news.ycombinator.com/jobs) pakai struktur HTML yang sama
        # dengan HN front page -- masih <tr class="athing"> -- jadi reuse
        # fungsi yang sama. Bedanya cuma URL sumbernya.
        return _parse_hn(raw, source_name)
    elif source_name == "We Work Remotely":
        return _parse_weworkremotely(raw, source_name)
    else:
        print(f"[parser] Tidak ada parser untuk source '{source_name}', dilewati.")
        return []


def _parse_remoteok(data, source_name):
    """
    Parse response JSON dari Remote OK API (https://remoteok.com/api) jadi
    list dict job. TIDAK pakai BeautifulSoup -- `data` di sini sudah Python
    object (list of dict) hasil fetch_json(), bukan HTML.

    Return: list of dict dengan key title, company, location, salary,
    tags, link, posted_at.

    CATATAN JUJUR: mapping field di bawah (position, tags, salary_min,
    dst) berdasarkan struktur Remote OK API yang saya ingat. Ini API
    publik yang cukup dikenal jadi saya cukup yakin bentuknya, tapi tetap
    tidak bisa saya verifikasi langsung field-fieldnya masih sama persis
    hari ini -- tidak ada akses jaringan di sisi saya. Kalau nanti hasil
    CSV banyak kolom kosong padahal job-nya jelas punya data itu (misal
    location selalu None), ini tempat pertama yang perlu dicek -- mungkin
    nama field-nya sudah berubah.
    """
    if not data:
        return []

    # Elemen PERTAMA di response Remote OK API adalah metadata (bukan job
    # sungguhan) -- bukan lowongan kerja. Jadi di-skip.
    jobs = data[1:]

    result = []
    for job in jobs:
        result.append({
            "source": source_name,
            "title": job.get("position"),
            "company": job.get("company"),
            "location": job.get("location"),
            "salary": format_salary(job.get("salary_min"), job.get("salary_max")),
            "tags": ", ".join(job.get("tags", [])) if job.get("tags") else "",
            "link": job.get("url"),
            "posted_at": job.get("date"),
        })

    return result


def _parse_hn(html, source_name):
    """
    Parse HTML Hacker News jadi list dict artikel.
    Return: list of dict dengan key title, link, score, author, age.
    Logic sama seperti scrape_hn.py sebelumnya, dipindah ke sini supaya
    semua selector tetap terkumpul di satu file (parser.py).
    """
    soup = BeautifulSoup(html, "html.parser")
    articles = soup.find_all("tr", class_="athing")

    data = []
    for article in articles:
        title_tag = article.find("span", class_="titleline")
        if not title_tag:
            continue

        link_tag = title_tag.find("a")
        if not link_tag:
            continue

        title = link_tag.get_text(strip=True)
        link = link_tag.get("href")

        subtext_row = article.find_next_sibling("tr")
        subtext = subtext_row.find("td", class_="subtext") if subtext_row else None

        score = None
        author = None
        age = None

        if subtext:
            score_tag = subtext.find("span", class_="score")
            if score_tag:
                score = score_tag.get_text(strip=True)

            author_tag = subtext.find("a", class_="hnuser")
            if author_tag:
                author = author_tag.get_text(strip=True)

            age_tag = subtext.find("span", class_="age")
            if age_tag:
                age_link = age_tag.find("a")
                age = age_link.get_text(strip=True) if age_link else age_tag.get_text(strip=True)

        data.append({
            "source": source_name,  # dari parameter, bukan hardcode
            "title": title,
            "link": link,
            "score": score,
            "author": author,
            "age": age,
        })

    return data


def _parse_weworkremotely(html, source_name):
    """
    Parse HTML We Work Remotely jadi list dict job.
    Return: list of dict dengan key title, company, location, tags, link.

    Struktur per job dikonfirmasi dari inspect element:

        <li class="new-listing-container ...">
          <a class="listing-link--unlocked" href="/remote-jobs/...">
            <h3 class="...header...title...">
              <span class="...header...title...text...">Judul</span>
            </h3>
            <p class="...company...name...">Nama Perusahaan</p>
            <p class="...company...headquarters...">Lokasi HQ</p>
            <div class="...categories...">
              <p class="...categories...category...">Contract</p>
              <p class="...categories...category...">$25,000 - $48,999 USD</p>
              <p class="...categories...category...">Anywhere in the World</p>
            </div>
          </a>
        </li>

    CATATAN PENTING soal cara selector ditulis di bawah: karena bukti yang
    saya dapat dari foto tidak bisa dipastikan 100% apakah pemisah kata di
    nama class-nya "-" (hyphen) atau "_" (underscore) -- foto kemarin
    kelihatan seperti "new-listing__header-title-text" tapi foto barusan
    kelihatan seperti "new-listing__header__title__text" -- saya sengaja
    TIDAK pakai exact match ke satu bentuk tertentu. Sebagai gantinya,
    saya cari elemen yang class-nya MENGANDUNG kata kunci tertentu
    (substring match via CSS selector [class*=...]), jadi selector ini
    akan tetap cocok baik pemisahnya "-" maupun "_".

    Kalau nanti tetap 0 hasil, kemungkinan bukan lagi soal hyphen/underscore,
    tapi soal kata kuncinya sendiri yang beda (misal bukan "title" tapi
    istilah lain) -- di titik itu perlu lihat HTML asli lagi, bukan
    utak-atik pemisah karakter.

    CATATAN LAMA (masih berlaku): jumlah <p> kategori per job tidak selalu
    sama (kadang cuma 2, kadang 3), urutannya tidak dipastikan konsisten,
    jadi semua teks kategori digabung ke kolom `tags` -- lebih aman
    daripada salah taruh ke kolom yang salah. Selector ini juga cuma
    menangkap listing yang "unlocked"; listing yang di-lock kemungkinan
    tidak ketangkep.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Anchor listing job: class mengandung "listing-link", DAN href mengarah
    # ke /remote-jobs/... -- dua syarat sekaligus biar tidak salah tangkap
    # elemen lain yang kebetulan mengandung kata "listing-link".
    job_links = [
        a for a in soup.select('a[class*="listing-link"]')
        if a.get("href", "").startswith("/remote-jobs/")
    ]

    data = []
    for a in job_links:
        title_tag = a.select_one('[class*="title"][class*="text"]')
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)

        company_tag = a.select_one('[class*="company"][class*="name"]')
        company = company_tag.get_text(strip=True) if company_tag else None

        location_tag = a.select_one('[class*="company"][class*="headquarters"]')
        location = location_tag.get_text(strip=True) if location_tag else None

        category_tags = a.select('[class*="categories"][class*="category"]')
        tags = ", ".join(c.get_text(strip=True) for c in category_tags)

        href = a.get("href")
        link = f"https://weworkremotely.com{href}" if href and not href.startswith("http") else href

        data.append({
            "source": source_name,
            "title": title,
            "company": company,
            "location": location,
            "tags": tags,
            "link": link,
        })

    return data