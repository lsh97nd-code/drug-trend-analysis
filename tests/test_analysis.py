import csv
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import analysis


def monthly_row(year=2017, month=1, **changes):
    row = dict(date=f"{year:04d}-{month:02d}", year=year, month=month,
               total=6, cannabis=1, narcotics=2, psychotropics=3)
    return {**row, **changes}


class MonthlyValidationTests(unittest.TestCase):
    def test_valid_months_across_new_year_keep_audit(self):
        audit = analysis.validate([monthly_row(2017, 12), monthly_row(2018, 1)])
        self.assertEqual((audit["rows"], audit["duplicates"], audit["missing"]), (2, 0, 0))
        self.assertEqual(audit["bad_sums"], [])
        self.assertEqual(audit["q1"], 6)

    def test_missing_and_invalid_fields(self):
        row = monthly_row()
        del row["cannabis"]
        cases = [
            ([], "행이 없습니다"),
            ([row], "필수 열.*cannabis"),
            ([monthly_row(date="2017-1")], "YYYY-MM"),
            ([monthly_row(date="2017-13")], "YYYY-MM"),
            ([monthly_row(date="2018-01")], "year/month"),
            ([monthly_row(date="2017-02")], "year/month"),
            ([monthly_row(total=-1)], "total.*정수"),
            ([monthly_row(cannabis=1.5)], "cannabis.*정수"),
            ([monthly_row(narcotics=True)], "narcotics.*정수"),
            ([monthly_row(psychotropics=None)], "psychotropics.*정수"),
            ([monthly_row(total=5)], "종류별 합계"),
        ]
        for rows, message in cases:
            with self.subTest(message=message, rows=rows), self.assertRaisesRegex(ValueError, message):
                analysis.validate(rows)

    def test_repeated_unsorted_and_skipped_dates(self):
        for month1, month2, message in [(1, 1, "중복"), (2, 1, "오름차순"), (1, 3, "누락")]:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                analysis.validate([monthly_row(2017, month1), monthly_row(2017, month2)])


class CsvValidationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "fixture.csv"

    def write(self, header, row):
        with self.path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerow(row)

    def test_monthly_csv_rejects_ambiguous_schema_and_malformed_numbers(self):
        header = list(analysis.MONTHLY_FIELDS)
        values = list(monthly_row().values())
        for fields, row, message in [
            (header[:-1], values[:-1], "필수 열.*psychotropics"),
            (header + ["total"], values + [6], "중복된 열"),
            (header, values[:-1], "열 개수"),
            (header, values + [4], "열 개수"),
            (header, [*values[:3], "", *values[4:]], "total.*정수"),
            (header, [*values[:3], "6.0", *values[4:]], "total.*정수"),
            (header, [*values[:3], -6, *values[4:]], "total.*음수"),
        ]:
            self.write(fields, row)
            with self.subTest(message=message, row=row), self.assertRaisesRegex(ValueError, message):
                analysis.load_monthly(self.path)

    def test_offense_breakdown_can_be_blank_only_in_2018(self):
        header = ["year", *analysis.OFFENSE_TYPES, "total"]
        blank = [""] * 7
        self.write(header, [2018, *blank, 12613])
        row, = analysis.load_offense(self.path)
        self.assertIsNone(row["manufacture"])
        self.assertEqual(row["total"], 12613)
        for values, message in [
            ([2018, 0, *blank[1:], 12613], "2018년 manufacture"),
            ([2019, *blank, 12613], "manufacture.*정수"),
            ([2019, *([1] * 7), 6], "범죄 유형별 합계"),
        ]:
            self.write(header, values)
            with self.subTest(values=values), self.assertRaisesRegex(ValueError, message):
                analysis.load_offense(self.path)


class ValidateOnlyCliTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        for script in ("analysis.py", "build_dataset.py"):
            shutil.copyfile(analysis.BASE_DIR / script, self.root / script)
        processed = self.root / "data" / "processed"
        processed.mkdir(parents=True)
        self.monthly = processed / analysis.MONTHLY_CSV.name
        self.offense = processed / analysis.OFFENSE_CSV.name
        shutil.copyfile(analysis.MONTHLY_CSV, self.monthly)
        shutil.copyfile(analysis.OFFENSE_CSV, self.offense)

    def run_cli(self):
        return subprocess.run(
            [sys.executable, "-B", "-S", "-X", "utf8", "analysis.py", "--validate-only"],
            cwd=self.root, capture_output=True, encoding="utf-8",
        )

    def test_real_inputs_validate_without_outputs_or_plot_dependencies(self):
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("2017-01 ~ 2025-12", result.stdout)
        self.assertIn("108", result.stdout)
        self.assertFalse((self.root / "images").exists())
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_missing_terminal_month_reports_period_error(self):
        lines = self.monthly.read_text(encoding="utf-8-sig").splitlines()
        self.monthly.write_text("\n".join(lines[:-1]), encoding="utf-8-sig")
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("2025-12", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_inconsistent_annual_total_is_rejected_even_with_valid_breakdown(self):
        with self.offense.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.reader(f))
        for row in rows[1:]:
            if row[0] == "2019":
                row[1] = str(int(row[1]) + 1)
                row[-2] = str(int(row[-2]) + 1)
        with self.offense.open("w", encoding="utf-8-sig", newline="") as f:
            csv.writer(f).writerows(rows)
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("2019년", result.stderr)
        self.assertIn("2명", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
