# utils.py
# Helper kecil yang dipakai lintas modul.

def format_salary(min_salary, max_salary):
    """
    Format angka salary mentah jadi string yang enak dibaca.

    Args:
        min_salary (int|float|None): Salary minimum, atau None/kosong.
        max_salary (int|float|None): Salary maximum, atau None/kosong.

    Returns:
        str: Contoh "$50k - $70k", "$50k+", "Up to $70k", atau
             "Not specified" kalau keduanya kosong.
    """
    def _to_k(n):
        return f"${int(n) // 1000}k"

    has_min = min_salary not in (None, "", 0)
    has_max = max_salary not in (None, "", 0)

    if has_min and has_max:
        return f"{_to_k(min_salary)} - {_to_k(max_salary)}"
    elif has_min:
        return f"{_to_k(min_salary)}+"
    elif has_max:
        return f"Up to {_to_k(max_salary)}"
    else:
        return "Not specified"

# Rencana ke depan (kalau memang dibutuhkan, bukan dipaksakan):
# - logger: logging terstruktur pengganti print()