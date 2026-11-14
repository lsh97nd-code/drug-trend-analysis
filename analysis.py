from __future__ import annotations

import argparse
import csv
import math
import re
from collections import defaultdict
from pathlib import Path

from build_dataset import DRUG_TYPES, OFFENSE_TYPES, YEARS

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"
IMG_DIR = BASE_DIR / "images"

MONTHLY_CSV = DATA_DIR / "monthly_drug_offenders_2017_2025.csv"
OFFENSE_CSV = DATA_DIR / "yearly_offense_type_2017_2025.csv"
DECOMP_CSV = DATA_DIR / "decomposition_2017_2025.csv"
MONTHLY_FIELDS = ("date", "year", "month", "total", *DRUG_TYPES)


def configure_korean_font():
    """Use an installed Korean font without depending on one OS."""
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    candidates = [
        Path("C:/Windows/Fonts/malgun.ttf"),
        Path("C:/Windows/Fonts/malgunbd.ttf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
        Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
    ]
    for path in candidates:
        if path.exists():
            try:
                font_manager.fontManager.addfont(str(path))
                font_name = font_manager.FontProperties(fname=str(path)).get_name()
                plt.rcParams["font.family"] = font_name
                break
            except Exception:
                pass
    plt.rcParams["axes.unicode_minus"] = False


def read_csv_rows(path, required):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, strict=True)
        headers = reader.fieldnames or []
        missing = set(required).difference(headers)
        if missing:
            raise ValueError(f"{path}: 필수 열 누락 ({', '.join(sorted(missing))})")
        if any(not field.strip() for field in headers) or len(set(headers)) != len(headers):
            raise ValueError(f"{path}: 비어 있거나 중복된 열 이름이 있습니다.")
        for row in reader:
            where = f"{path}:{reader.line_num}"
            if None in row or None in row.values():
                raise ValueError(f"{where}: 데이터 열 개수가 헤더와 다릅니다.")
            yield where, row


def parse_count(value, field, where):
    if not re.fullmatch(r"[+-]?[0-9]+", value.strip()):
        raise ValueError(f"{where}: {field} 값은 정수여야 합니다 ({value!r}).")
    number = int(value)
    if number < 0:
        raise ValueError(f"{where}: {field} 값은 음수일 수 없습니다 ({number}).")
    return number


def load_monthly(path=None):
    rows = []
    for where, row in read_csv_rows(path or MONTHLY_CSV, MONTHLY_FIELDS):
        for field in MONTHLY_FIELDS[1:]:
            row[field] = parse_count(row[field], field, where)
        row["date"] = row["date"].strip()
        rows.append(row)
    return rows


def load_offense(path=None):
    rows = []
    for where, row in read_csv_rows(path or OFFENSE_CSV, ("year", *OFFENSE_TYPES, "total")):
        year = row["year"] = parse_count(row["year"], "year", where)
        row["total"] = parse_count(row["total"], "total", where)
        for field in OFFENSE_TYPES:
            if year == 2018:
                if row[field].strip():
                    raise ValueError(f"{where}: 2018년 {field} 값은 원자료에 없어 공란이어야 합니다.")
                row[field] = None
            else:
                row[field] = parse_count(row[field], field, where)
        if year != 2018 and sum(row[k] for k in OFFENSE_TYPES) != row["total"]:
            raise ValueError(f"{where}: {year}년 범죄 유형별 합계가 전체와 다릅니다.")
        rows.append(row)
    return rows


def percentile(values, q):
    values = sorted(values)
    pos = (len(values) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return float(values[lo])
    return values[lo] * (hi - pos) + values[hi] * (pos - lo)


def validate(rows):
    if not rows:
        raise ValueError("월별 데이터에 행이 없습니다.")
    previous = None
    seen = set()
    for line, row in enumerate(rows, start=2):
        missing = set(MONTHLY_FIELDS).difference(row)
        if missing:
            raise ValueError(f"월별 데이터 {line}행: 필수 열 누락 ({', '.join(sorted(missing))})")
        date = row["date"]
        for field in MONTHLY_FIELDS[1:]:
            value = row[field]
            if type(value) is not int or value < 0:
                raise ValueError(f"월별 데이터 {line}행: {field} 값은 0 이상의 정수여야 합니다.")
        year, month = row["year"], row["month"]
        if not isinstance(date, str) or not re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", date):
            raise ValueError(f"월별 데이터 {line}행: date 값은 YYYY-MM이어야 합니다 ({date!r}).")
        if year < 1 or date != f"{year:04d}-{month:02d}":
            raise ValueError(f"{date}: date와 year/month가 일치하지 않습니다 ({year}, {month}).")
        if date in seen:
            raise ValueError(f"{date}: 중복 월입니다.")
        seen.add(date)
        index = year * 12 + month - 1
        if previous is not None:
            if index < previous:
                raise ValueError(f"{date}: 월별 데이터가 날짜 오름차순이 아닙니다.")
            if index != previous + 1:
                raise ValueError(f"{date}: 앞에 누락된 월이 있습니다.")
        previous = index
        if sum(row[k] for k in DRUG_TYPES) != row["total"]:
            raise ValueError(f"{date}: 종류별 합계가 전체와 다릅니다.")

    total_vals = [r["total"] for r in rows]
    q1 = percentile(total_vals, 0.25)
    q3 = percentile(total_vals, 0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    outliers = [
        (r["date"], r["total"])
        for r in rows
        if r["total"] < lower or r["total"] > upper
    ]
    return {
        "rows": len(rows),
        "duplicates": 0,
        "missing": 0,
        "bad_sums": [],
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "lower": lower,
        "upper": upper,
        "outliers": outliers,
    }


def rolling_mean(values, window=12):
    result = [math.nan] * len(values)
    for i in range(window - 1, len(values)):
        result[i] = sum(values[i-window+1:i+1]) / window
    return result


def yoy_rate(values, lag=12):
    result = [math.nan] * len(values)
    for i in range(lag, len(values)):
        prev = values[i-lag]
        result[i] = ((values[i] - prev) / prev * 100) if prev else math.nan
    return result


def classical_additive_decomposition(rows):
    """12-month classical additive decomposition.

    Trend: centered 2x12 moving average.
    Seasonality: monthly mean of detrended values, adjusted to sum to zero.
    Residual: observed - trend - seasonal.
    """
    import numpy as np

    values = np.array([r["total"] for r in rows], dtype=float)
    months = np.array([r["month"] for r in rows])

    # Centered 2x12 moving average = 13-point weights:
    # endpoints 1/24, middle 11 values 1/12, endpoint 1/24.
    weights = np.array([1/24] + [1/12] * 11 + [1/24], dtype=float)
    trend = np.full(len(values), np.nan)
    for i in range(6, len(values) - 6):
        trend[i] = np.dot(values[i-6:i+7], weights)

    detrended = values - trend
    seasonal_by_month = np.zeros(12)
    for month in range(1, 13):
        mask = (months == month) & ~np.isnan(trend)
        seasonal_by_month[month-1] = np.nanmean(detrended[mask])
    seasonal_by_month -= seasonal_by_month.mean()

    seasonal = np.array([seasonal_by_month[m-1] for m in months])
    residual = values - trend - seasonal
    return values, trend, seasonal_by_month, seasonal, residual


def save_decomposition_csv(rows, observed, trend, seasonal, residual):
    import numpy as np

    with DECOMP_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "observed", "trend", "seasonal", "residual"])
        for i, r in enumerate(rows):
            writer.writerow([
                r["date"],
                int(observed[i]),
                "" if np.isnan(trend[i]) else f"{trend[i]:.3f}",
                f"{seasonal[i]:.3f}",
                "" if np.isnan(residual[i]) else f"{residual[i]:.3f}",
            ])


def year_ticks(rows):
    import numpy as np

    labels = [r["date"] for r in rows]
    ticks = np.arange(0, len(rows), 12)
    return ticks, [labels[i][:4] for i in ticks]


def plot_monthly(rows):
    import matplotlib.pyplot as plt
    import numpy as np

    x = np.arange(len(rows))
    y = np.array([r["total"] for r in rows])
    ticks, labels = year_ticks(rows)
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(x, y)
    ax.set_title("월별 마약류사범 단속 추이 (2017-2025)")
    ax.set_ylabel("단속인원(명)")
    ax.set_xticks(ticks, labels)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(IMG_DIR / "06_monthly_offender_trend.png", dpi=160)
    plt.close(fig)


def plot_moving_average(rows):
    import matplotlib.pyplot as plt
    import numpy as np

    x = np.arange(len(rows))
    y = [r["total"] for r in rows]
    ma = rolling_mean(y, 12)
    ticks, labels = year_ticks(rows)
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(x, y, alpha=0.45, label="월별 단속인원")
    ax.plot(x, ma, linewidth=2.2, label="12개월 이동평균")
    ax.set_title("월별 단속인원과 12개월 이동평균")
    ax.set_ylabel("단속인원(명)")
    ax.set_xticks(ticks, labels)
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(IMG_DIR / "07_moving_average.png", dpi=160)
    plt.close(fig)


def plot_offense_share(offense_rows):
    import matplotlib.pyplot as plt
    import numpy as np

    categories = [
        ("manufacture", "밀조"), ("smuggling", "밀수"), ("dealing", "밀매"),
        ("illegal_cultivation", "밀경"), ("use", "투약"),
        ("possession", "소지"), ("other", "기타"),
    ]
    usable = [r for r in offense_rows if r["manufacture"] is not None]
    years = [r["year"] for r in usable]
    bottoms = np.zeros(len(usable))
    fig, ax = plt.subplots(figsize=(13, 7))
    for key, label in categories:
        vals = np.array([r[key] / r["total"] * 100 for r in usable])
        ax.bar(years, vals, bottom=bottoms, label=label)
        bottoms += vals
    ax.set_title("연간 마약류사범 범죄 유형별 구성비")
    ax.set_ylabel("구성비(%)")
    ax.set_ylim(0, 100)
    ax.set_xticks(range(2017, 2026))
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    ax.text(
        2018, 50, "2018\n원자료 불일치로\n유형별 값 미사용",
        ha="center", va="center", fontsize=9,
    )
    fig.tight_layout()
    fig.savefig(IMG_DIR / "08_offense_type_share.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_period_comparison(rows):
    import matplotlib.pyplot as plt

    periods = [
        ("코로나 이전\n2017-2019", 2017, 2019),
        ("유행·제약\n2020-2022", 2020, 2022),
        ("이후\n2023-2025", 2023, 2025),
    ]
    means = []
    for _, a, b in periods:
        vals = [r["total"] for r in rows if a <= r["year"] <= b]
        means.append(sum(vals) / len(vals))
    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.bar([p[0] for p in periods], means)
    ax.set_title("분석 구간별 월평균 마약류사범 단속인원")
    ax.set_ylabel("월평균 단속인원(명)")
    for bar, value in zip(bars, means):
        ax.text(
            bar.get_x() + bar.get_width()/2,
            bar.get_height(),
            f"{value:,.1f}",
            ha="center",
            va="bottom",
        )
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(IMG_DIR / "09_period_comparison.png", dpi=160)
    plt.close(fig)


def plot_drug_type(rows):
    import matplotlib.pyplot as plt
    import numpy as np

    x = np.arange(len(rows))
    ticks, labels = year_ticks(rows)
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(x, [r["cannabis"] for r in rows], label="대마")
    ax.plot(x, [r["narcotics"] for r in rows], label="마약")
    ax.plot(x, [r["psychotropics"] for r in rows], label="향정신성의약품")
    ax.set_title("마약류 종류별 월간 단속 추이")
    ax.set_ylabel("단속인원(명)")
    ax.set_xticks(ticks, labels)
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(IMG_DIR / "10_drug_type_trend.png", dpi=160)
    plt.close(fig)


def plot_yoy_change(rows):
    import matplotlib.pyplot as plt
    import numpy as np

    x = np.arange(len(rows))
    y = [r["total"] for r in rows]
    yoy = yoy_rate(y, 12)
    ticks, labels = year_ticks(rows)
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.axhline(0, linewidth=1)
    ax.plot(x, yoy)
    ax.set_title("마약류사범 단속인원 전년 동월 대비 변화율")
    ax.set_ylabel("전년 동월 대비(%)")
    ax.set_xticks(ticks, labels)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(IMG_DIR / "11_yoy_change_rate.png", dpi=160)
    plt.close(fig)


def plot_month_seasonality(rows):
    import matplotlib.pyplot as plt

    by_month = defaultdict(list)
    for r in rows:
        by_month[r["month"]].append(r["total"])
    means = [sum(by_month[m]) / len(by_month[m]) for m in range(1, 13)]
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar([f"{m}월" for m in range(1, 13)], means)
    ax.set_title("2017-2025 달력 월별 평균 단속인원")
    ax.set_ylabel("평균 단속인원(명)")
    for bar, value in zip(bars, means):
        ax.text(
            bar.get_x() + bar.get_width()/2,
            bar.get_height(),
            f"{value:,.0f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(IMG_DIR / "12_month_seasonality.png", dpi=160)
    plt.close(fig)


def plot_decomposition(rows, observed, trend, seasonal_by_month, residual):
    import matplotlib.pyplot as plt
    import numpy as np

    x = np.arange(len(rows))
    ticks, labels = year_ticks(rows)

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(x, observed)
    ax.set_title("시계열 분해 - 원자료(Observed)")
    ax.set_ylabel("단속인원(명)")
    ax.set_xticks(ticks, labels)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(IMG_DIR / "13_decomposition_observed.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(x, trend)
    ax.set_title("시계열 분해 - 추세(Trend)")
    ax.set_ylabel("추세 단속인원(명)")
    ax.set_xticks(ticks, labels)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(IMG_DIR / "14_decomposition_trend.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar([f"{m}월" for m in range(1, 13)], seasonal_by_month)
    ax.axhline(0, linewidth=1)
    ax.set_title("시계열 분해 - 월별 계절성(Seasonality)")
    ax.set_ylabel("추세 대비 월별 효과(명)")
    for bar, value in zip(bars, seasonal_by_month):
        ax.text(
            bar.get_x() + bar.get_width()/2,
            value,
            f"{value:+.0f}",
            ha="center",
            va="bottom" if value >= 0 else "top",
            fontsize=8,
        )
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(IMG_DIR / "15_decomposition_seasonality.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.axhline(0, linewidth=1)
    ax.plot(x, residual)
    ax.set_title("시계열 분해 - 잔차(Residual)")
    ax.set_ylabel("잔차(명)")
    ax.set_xticks(ticks, labels)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(IMG_DIR / "16_decomposition_residual.png", dpi=160)
    plt.close(fig)


def write_summary(rows, audit, trend, seasonal_by_month, residual):
    import numpy as np

    period_defs = [
        ("코로나 이전(2017-2019)", 2017, 2019),
        ("코로나 유행·제약(2020-2022)", 2020, 2022),
        ("코로나 이후(2023-2025)", 2023, 2025),
    ]
    lines = [
        f"행 수: {audit['rows']}",
        f"중복: {audit['duplicates']}",
        f"핵심 월별 데이터 결측치: {audit['missing']}",
        f"대마+마약+향정=전체 불일치: {len(audit['bad_sums'])}",
        (
            f"IQR 기준(total): Q1={audit['q1']:.2f}, Q3={audit['q3']:.2f}, "
            f"상한={audit['upper']:.2f}; 이상치 후보={audit['outliers']}"
        ),
        "",
    ]
    for name, a, b in period_defs:
        vals = [r["total"] for r in rows if a <= r["year"] <= b]
        lines.append(f"{name}: 월평균 {sum(vals)/len(vals):,.1f}명")

    top = sorted(rows, key=lambda r: r["total"], reverse=True)[:5]
    lines += [
        "",
        "월별 단속인원 상위 5개: " +
        ", ".join(f"{r['date']} {r['total']:,}명" for r in top),
        "",
        "[시계열 분해 보너스]",
    ]

    valid = np.where(~np.isnan(trend))[0]
    min_i = valid[np.argmin(trend[valid])]
    max_i = valid[np.argmax(trend[valid])]
    lines.append(f"분해 추세 최저: {rows[min_i]['date']} {trend[min_i]:,.1f}명")
    lines.append(f"분해 추세 최고: {rows[max_i]['date']} {trend[max_i]:,.1f}명")
    max_month = int(np.argmax(seasonal_by_month)) + 1
    min_month = int(np.argmin(seasonal_by_month)) + 1
    lines.append(
        f"계절성 최고: {max_month}월 {seasonal_by_month[max_month-1]:+,.1f}명; "
        f"최저: {min_month}월 {seasonal_by_month[min_month-1]:+,.1f}명"
    )
    valid_resid = valid[~np.isnan(residual[valid])]
    top_resid = valid_resid[np.argsort(np.abs(residual[valid_resid]))[::-1][:5]]
    lines.append(
        "절대 잔차 상위 5개: " +
        ", ".join(f"{rows[i]['date']} {residual[i]:+,.1f}명" for i in top_resid)
    )

    (BASE_DIR / "analysis_summary.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main(validate_only=False):
    rows = load_monthly()
    audit = validate(rows)
    offense_rows = load_offense()
    if rows[0]["date"] != f"{YEARS[0]}-01" or rows[-1]["date"] != f"{YEARS[-1]}-12":
        raise ValueError(f"월별 데이터는 {YEARS[0]}-01부터 {YEARS[-1]}-12까지 필요합니다.")
    if [row["year"] for row in offense_rows] != list(YEARS):
        raise ValueError(f"범죄 유형 CSV에는 {YEARS[0]}~{YEARS[-1]}년이 한 번씩 오름차순으로 필요합니다.")
    annual_totals = defaultdict(int)
    for row in rows:
        annual_totals[row["year"]] += row["total"]
    for offense in offense_rows:
        year = offense["year"]
        expected_gap = 2 if year == 2019 else 0
        if annual_totals[year] - offense["total"] != expected_gap:
            raise ValueError(f"{year}년 월별 합계와 연간 누계의 차이는 {expected_gap}명이어야 합니다.")

    print("=== 데이터 검증 ===")
    print(f"기간: {rows[0]['date']} ~ {rows[-1]['date']}")
    print(f"행 수: {audit['rows']}")
    print(f"중복: {audit['duplicates']}")
    print(f"핵심 데이터 결측: {audit['missing']}")
    print(f"종류합계 불일치: {audit['bad_sums']}")
    print(f"IQR 이상치 후보: {audit['outliers']}")
    if validate_only:
        return

    configure_korean_font()
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    plot_monthly(rows)
    plot_moving_average(rows)
    plot_offense_share(offense_rows)
    plot_period_comparison(rows)
    plot_drug_type(rows)
    plot_yoy_change(rows)
    plot_month_seasonality(rows)

    observed, trend, seasonal_by_month, seasonal, residual = (
        classical_additive_decomposition(rows)
    )
    save_decomposition_csv(rows, observed, trend, seasonal, residual)
    plot_decomposition(rows, observed, trend, seasonal_by_month, residual)
    write_summary(rows, audit, trend, seasonal_by_month, residual)

    print("기본 그래프 7개 + 시계열 분해 그래프 4개 생성 완료: images/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="2017~2025년 마약류사범 통계 분석")
    parser.add_argument("--validate-only", action="store_true", help="입력 CSV만 검증합니다.")
    args = parser.parse_args()
    try:
        main(validate_only=args.validate_only)
    except (ValueError, OSError, csv.Error) as error:
        parser.exit(1, f"오류: {error}\n")
