from __future__ import annotations

import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Verified from the monthly tables in each December report.
# 2018-12 type values (cannabis/narcotics/psychotropics) were derived from
# 2018 annual totals printed in the 2019-12 comparison table minus 2018 Jan-Nov.
MONTHLY = {
    2017: {
        "total": [1059, 891, 1218, 1254, 1510, 1622, 1613, 1387, 1200, 797, 891, 681],
        "cannabis": [115, 85, 116, 183, 187, 182, 221, 176, 132, 99, 138, 94],
        "narcotics": [22, 26, 31, 22, 98, 468, 496, 199, 46, 17, 34, 16],
        "psychotropics": [922, 780, 1071, 1049, 1225, 972, 896, 1012, 1022, 681, 719, 571],
    },
    2018: {
        "total": [829, 704, 945, 992, 1024, 1447, 1486, 1438, 925, 1209, 884, 730],
        "cannabis": [137, 71, 128, 130, 142, 156, 135, 160, 136, 140, 102, 96],
        "narcotics": [32, 50, 34, 28, 49, 319, 491, 311, 61, 32, 32, 28],
        "psychotropics": [660, 583, 783, 834, 833, 972, 860, 967, 728, 1037, 750, 606],
    },
    2019: {
        "total": [808, 616, 960, 1524, 3091, 1614, 1537, 1336, 1109, 1213, 1310, 928],
        "cannabis": [108, 73, 160, 218, 500, 200, 177, 258, 257, 230, 304, 145],
        "narcotics": [42, 22, 29, 37, 298, 336, 437, 315, 74, 68, 54, 93],
        "psychotropics": [658, 521, 771, 1269, 2293, 1078, 923, 763, 778, 915, 952, 690],
    },
    2020: {
        "total": [898, 865, 945, 1070, 1267, 1909, 2567, 1662, 1296, 1315, 1593, 2663],
        "cannabis": [163, 129, 200, 127, 151, 228, 267, 399, 240, 351, 417, 540],
        "narcotics": [35, 23, 37, 39, 92, 467, 998, 230, 70, 74, 49, 84],
        "psychotropics": [700, 713, 708, 904, 1024, 1214, 1302, 1033, 986, 890, 1127, 2039],
    },
    2021: {
        "total": [1075, 583, 1074, 1161, 1413, 2259, 1796, 1327, 1191, 1548, 1615, 1111],
        "cannabis": [244, 110, 213, 192, 434, 621, 292, 328, 256, 412, 398, 277],
        "narcotics": [86, 23, 22, 76, 114, 282, 622, 197, 78, 119, 70, 56],
        "psychotropics": [745, 450, 839, 893, 865, 1356, 882, 802, 857, 1017, 1147, 778],
    },
    2022: {
        "total": [1050, 914, 1113, 1230, 1638, 2630, 2000, 1658, 1475, 1474, 1891, 1322],
        "cannabis": [248, 231, 222, 247, 336, 512, 340, 298, 270, 251, 575, 279],
        "narcotics": [84, 98, 69, 60, 152, 691, 689, 341, 157, 84, 76, 50],
        "psychotropics": [718, 585, 822, 923, 1150, 1427, 971, 1019, 1048, 1139, 1240, 993],
    },
    2023: {
        "total": [1314, 1286, 1524, 1463, 1807, 2858, 4220, 3715, 2043, 2163, 2795, 2423],
        "cannabis": [294, 233, 233, 213, 201, 306, 356, 570, 328, 304, 559, 488],
        "narcotics": [48, 114, 96, 50, 188, 869, 1425, 546, 290, 120, 134, 90],
        "psychotropics": [972, 939, 1195, 1200, 1418, 1683, 2439, 2599, 1425, 1739, 2102, 1845],
    },
    2024: {
        "total": [2017, 1471, 1552, 1780, 2157, 2081, 2834, 2260, 1401, 1884, 1908, 1677],
        "cannabis": [413, 247, 226, 219, 262, 253, 406, 292, 191, 281, 294, 233],
        "narcotics": [72, 53, 56, 75, 117, 344, 569, 281, 132, 111, 74, 70],
        "psychotropics": [1532, 1171, 1270, 1486, 1778, 1484, 1859, 1687, 1078, 1492, 1540, 1374],
    },
    2025: {
        "total": [1685, 1494, 1477, 1811, 1922, 2089, 3221, 1836, 2190, 1949, 2047, 1682],
        "cannabis": [178, 151, 203, 197, 190, 184, 305, 184, 234, 185, 235, 213],
        "narcotics": [69, 46, 46, 80, 122, 329, 484, 207, 176, 70, 55, 48],
        "psychotropics": [1438, 1297, 1228, 1534, 1610, 1576, 2432, 1445, 1780, 1694, 1757, 1421],
    },
}

PUBLISHED_ANNUAL_TOTAL = {
    2017: 14123, 2018: 12613, 2019: 16044, 2020: 18050, 2021: 16153,
    2022: 18395, 2023: 27611, 2024: 23022, 2025: 23403,
}

# December annual cumulative offense-type table.
# The 2018 December PDF repeats Jan-Nov offense-type cumulative values, so the
# seven offense-type cells are intentionally left blank rather than guessed.
YEARLY_OFFENSE = {
    2017: [3, 481, 3471, 1030, 7346, 1002, 790, 14123],
    2018: [None, None, None, None, None, None, None, 12613],
    2019: [5, 783, 3437, 1161, 8210, 1185, 1263, 16044],
    2020: [9, 837, 3947, 1805, 9044, 1115, 1293, 18050],
    2021: [9, 807, 3229, 1151, 8522, 1214, 1221, 16153],
    2022: [6, 1392, 3492, 1712, 8489, 1032, 2272, 18395],
    2023: [6, 1235, 7904, 3081, 10899, 1859, 2627, 27611],
    2024: [19, 1126, 6593, 1123, 9528, 1888, 2745, 23022],
    2025: [25, 1772, 4980, 976, 8798, 1747, 5105, 23403],
}


def write_monthly() -> Path:
    rows = []
    for year in range(2017, 2026):
        d = MONTHLY[year]
        for idx in range(12):
            c = d["cannabis"][idx]
            n = d["narcotics"][idx]
            p = d["psychotropics"][idx]
            total = d["total"][idx]
            if c + n + p != total:
                raise ValueError(f"Monthly sum mismatch: {year}-{idx+1:02d}")
            rows.append({
                "date": f"{year}-{idx+1:02d}",
                "year": year,
                "month": idx + 1,
                "total": total,
                "cannabis": c,
                "narcotics": n,
                "psychotropics": p,
            })

    out = OUT_DIR / "monthly_drug_offenders_2017_2025.csv"
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return out


def write_offense() -> Path:
    out = OUT_DIR / "yearly_offense_type_2017_2025.csv"
    fields = [
        "year", "manufacture", "smuggling", "dealing", "illegal_cultivation",
        "use", "possession", "other", "total", "source_note",
    ]
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for year, values in YEARLY_OFFENSE.items():
            *types, total = values
            if year != 2018 and sum(types) != total:
                raise ValueError(f"Offense-type sum mismatch: {year}")
            note = (
                "2018 December source repeats Jan-Nov cumulative offense-type values; "
                "breakdown left blank pending corrected source."
                if year == 2018
                else "December report annual cumulative offense-type table."
            )
            writer.writerow({
                "year": year,
                "manufacture": types[0],
                "smuggling": types[1],
                "dealing": types[2],
                "illegal_cultivation": types[3],
                "use": types[4],
                "possession": types[5],
                "other": types[6],
                "total": total,
                "source_note": note,
            })
    return out


def print_audit() -> None:
    print("[Annual reconciliation]")
    for year in range(2017, 2026):
        monthly_sum = sum(MONTHLY[year]["total"])
        published = PUBLISHED_ANNUAL_TOTAL[year]
        delta = monthly_sum - published
        flag = "OK" if delta == 0 else "SOURCE DIFFERENCE"
        print(f"{year}: monthly sum={monthly_sum:,}, published cumulative={published:,}, delta={delta:+,} [{flag}]")
    print("\nNote: 2019 monthly table sums to 16,046 while the report's annual cumulative is 16,044.")
    print("The monthly series keeps the published monthly values and records the 2-person discrepancy as a source revision/inconsistency.")


if __name__ == "__main__":
    print(f"Created: {write_monthly()}")
    print(f"Created: {write_offense()}")
    print_audit()
