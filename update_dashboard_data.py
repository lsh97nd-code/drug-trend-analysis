from __future__ import annotations

import argparse
import csv
import json
import os
import tempfile
from pathlib import Path

import analysis


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DASHBOARD_OUTPUT = BASE_DIR / "dashboard" / "data.js"
DEFAULT_DOCS_OUTPUT = BASE_DIR / "docs" / "data.js"


def render_data_js(monthly_rows, offense_rows):
    """Return the validated dashboard payload in a deterministic format."""
    monthly = [
        {field: row[field] for field in analysis.MONTHLY_FIELDS}
        for row in monthly_rows
    ]
    offense = []
    for row in offense_rows:
        item = {
            "year": row["year"],
            **{field: row[field] for field in analysis.OFFENSE_TYPES},
            "total": row["total"],
        }
        if "source_note" in row:
            item["source_note"] = row["source_note"].strip()
        offense.append(item)

    compact = {"ensure_ascii": False, "separators": (",", ":")}
    return (
        f"window.MONTHLY_DATA = {json.dumps(monthly, **compact)};\n"
        f"window.OFFENSE_DATA = {json.dumps(offense, **compact)};\n"
    )


def _stage_bytes(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    ) as temporary:
        temporary.write(content)
        temporary.flush()
        os.fsync(temporary.fileno())
        return Path(temporary.name)


def _stage_text(path, text):
    return _stage_bytes(path, text.encode("utf-8"))


def _restore(path, original):
    if original is None:
        path.unlink(missing_ok=True)
        return
    staged = _stage_bytes(path, original)
    os.replace(staged, path)


def write_pair_atomic(first, second, text):
    """Replace both mirrors, restoring prior bytes if either replacement fails."""
    first = Path(first)
    second = Path(second)
    if first.resolve() == second.resolve():
        raise ValueError("dashboard와 docs 출력 경로는 서로 달라야 합니다.")

    originals = {
        first: first.read_bytes() if first.exists() else None,
        second: second.read_bytes() if second.exists() else None,
    }
    staged = {}
    replaced = []
    try:
        for path in (first, second):
            staged[path] = _stage_text(path, text)
        for path in (first, second):
            os.replace(staged[path], path)
            replaced.append(path)
    except OSError:
        for path in reversed(replaced):
            _restore(path, originals[path])
        raise
    finally:
        for temporary in staged.values():
            temporary.unlink(missing_ok=True)


def update_dashboard_data(
    monthly_path=analysis.MONTHLY_CSV,
    offense_path=analysis.OFFENSE_CSV,
    dashboard_output=DEFAULT_DASHBOARD_OUTPUT,
    docs_output=DEFAULT_DOCS_OUTPUT,
    *,
    check=False,
):
    """Validate source CSVs and update the two dashboard payload mirrors."""
    monthly_rows = analysis.load_monthly(monthly_path)
    offense_rows = analysis.load_offense(offense_path)
    analysis.validate_dataset(monthly_rows, offense_rows)
    payload = render_data_js(monthly_rows, offense_rows)

    outputs = (Path(dashboard_output), Path(docs_output))
    if outputs[0].resolve() == outputs[1].resolve():
        raise ValueError("dashboard와 docs 출력 경로는 서로 달라야 합니다.")
    if check:
        stale = [
            str(path)
            for path in outputs
            if not path.exists() or path.read_text(encoding="utf-8") != payload
        ]
        if stale:
            raise ValueError("갱신이 필요한 출력: " + ", ".join(stale))
    else:
        write_pair_atomic(*outputs, payload)

    return {
        "start": monthly_rows[0]["date"],
        "end": monthly_rows[-1]["date"],
        "months": len(monthly_rows),
        "years": len(offense_rows),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="검증된 CSV로 dashboard/docs data.js를 함께 갱신합니다."
    )
    parser.add_argument("--monthly", type=Path, default=analysis.MONTHLY_CSV)
    parser.add_argument("--offense", type=Path, default=analysis.OFFENSE_CSV)
    parser.add_argument(
        "--dashboard-output", type=Path, default=DEFAULT_DASHBOARD_OUTPUT
    )
    parser.add_argument("--docs-output", type=Path, default=DEFAULT_DOCS_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="파일을 쓰지 않고 두 data.js가 입력 CSV와 일치하는지만 확인합니다.",
    )
    args = parser.parse_args(argv)
    try:
        summary = update_dashboard_data(
            args.monthly,
            args.offense,
            args.dashboard_output,
            args.docs_output,
            check=args.check,
        )
    except (ValueError, OSError, csv.Error) as error:
        parser.exit(1, f"오류: {error}\n")

    action = "일치 확인" if args.check else "갱신 완료"
    print(
        f"data.js {action}: {summary['start']} ~ {summary['end']} "
        f"({summary['months']}개월, {summary['years']}개 연도)"
    )


if __name__ == "__main__":
    main()
