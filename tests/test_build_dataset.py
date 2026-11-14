import csv
import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import build_dataset as dataset


class BuildDatasetTests(unittest.TestCase):
    def setUp(self):
        for name in ("MONTHLY", "PUBLISHED_ANNUAL_TOTAL", "YEARLY_OFFENSE"):
            table = deepcopy(getattr(dataset, name))
            replacement = patch.object(dataset, name, table)
            replacement.start()
            self.addCleanup(replacement.stop)

    def test_exports_preserve_source_values_and_missing_offense_counts(self):
        with TemporaryDirectory() as folder:
            out = Path(folder) / "processed"
            with dataset.write_monthly(out).open(encoding="utf-8-sig", newline="") as f:
                monthly = list(csv.DictReader(f))
            with dataset.write_offense(out).open(encoding="utf-8-sig", newline="") as f:
                offenses = list(csv.DictReader(f))

        self.assertEqual(len(monthly), 108)
        self.assertEqual([monthly[0]["date"], monthly[-1]["date"]], ["2017-01", "2025-12"])
        self.assertEqual(sum(int(row["total"]) for row in monthly if row["year"] == "2019"), 16046)
        self.assertEqual([int(row["year"]) for row in offenses], list(range(2017, 2026)))
        self.assertEqual(offenses[2]["total"], "16044")
        self.assertEqual(offenses[1]["total"], "12613")
        self.assertEqual([offenses[1][field] for field in dataset.OFFENSE_TYPES], [""] * 7)

    def test_each_table_requires_exact_year_set(self):
        for name in ("MONTHLY", "PUBLISHED_ANNUAL_TOTAL", "YEARLY_OFFENSE"):
            for extra in (False, True):
                with self.subTest(table=name, extra=extra):
                    table = getattr(dataset, name).copy()
                    if extra:
                        table[2026] = table[2025]
                    else:
                        del table[2025]
                    with patch.object(dataset, name, table), self.assertRaisesRegex(ValueError, "2017.2025"):
                        dataset.validate_source_tables()

    def test_monthly_series_must_have_four_fields_and_twelve_counts(self):
        series = dataset.MONTHLY[2020]
        for values in (series["cannabis"][:-1], [*series["cannabis"], 0], None):
            with self.subTest(values=values), patch.dict(series, cannabis=values):
                with self.assertRaisesRegex(ValueError, "2020 cannabis.*12"):
                    dataset.validate_source_tables()
        del series["cannabis"]
        with self.assertRaisesRegex(ValueError, "2020.*cannabis"):
            dataset.validate_source_tables()

    def test_counts_require_nonnegative_integers(self):
        for table, year, field, label in (
            (dataset.MONTHLY[2017]["total"], 0, 1059, "2017-01 total"),
            (dataset.PUBLISHED_ANNUAL_TOTAL, 2020, 18050, "2020 published annual total"),
            (dataset.YEARLY_OFFENSE[2020], -1, 18050, "2020 offense total"),
            (dataset.YEARLY_OFFENSE[2022], 0, 6, "2022 offense manufacture"),
        ):
            for bad in (float(field), -1, True, None):
                with self.subTest(label=label, value=bad):
                    table[year] = bad
                    with self.assertRaisesRegex(ValueError, label):
                        dataset.validate_source_tables()
            table[year] = field

    def test_drug_types_must_sum_to_monthly_total(self):
        dataset.MONTHLY[2023]["cannabis"][5] += 1
        with self.assertRaisesRegex(ValueError, "2023-06.*sum"):
            dataset.validate_source_tables()

    def test_only_2019_has_a_plus_two_annual_difference(self):
        for year, change in ((2019, 2), (2019, 4), (2021, -2)):
            with self.subTest(year=year, change=change):
                total = dataset.PUBLISHED_ANNUAL_TOTAL[year] + change
                with patch.dict(dataset.PUBLISHED_ANNUAL_TOTAL, {year: total}):
                    with self.assertRaisesRegex(ValueError, f"{year}.*monthly sum"):
                        dataset.validate_source_tables()

    def test_offense_breakdown_and_total_are_validated_before_files_are_written(self):
        with TemporaryDirectory() as folder:
            out = Path(folder)
            paths = [dataset.write_monthly(out), dataset.write_offense(out)]
            for path in paths:
                path.write_bytes(b"existing output")
            for year, values, reason in (
                (2018, [0, *dataset.YEARLY_OFFENSE[2018][1:]], "blank"),
                (2024, dataset.YEARLY_OFFENSE[2024][:-1], "seven"),
                (2024, [*dataset.YEARLY_OFFENSE[2024][:-1], 999], "published total"),
                (2025, [0, *dataset.YEARLY_OFFENSE[2025][1:]], "sum"),
            ):
                with self.subTest(year=year, reason=reason), patch.dict(dataset.YEARLY_OFFENSE, {year: values}):
                    for writer in (dataset.write_monthly, dataset.write_offense):
                        with self.assertRaisesRegex(ValueError, f"{year}.*{reason}"):
                            writer(out)
                    self.assertEqual([path.read_bytes() for path in paths], [b"existing output"] * 2)


if __name__ == "__main__":
    unittest.main()
