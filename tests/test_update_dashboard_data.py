import csv
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import analysis
import update_dashboard_data as updater


class DashboardDataUpdateTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.monthly = self.root / "monthly.csv"
        self.offense = self.root / "offense.csv"
        shutil.copyfile(analysis.MONTHLY_CSV, self.monthly)
        shutil.copyfile(analysis.OFFENSE_CSV, self.offense)
        self.dashboard = self.root / "dashboard" / "data.js"
        self.docs = self.root / "docs" / "data.js"

    def append_year(self, year):
        with self.monthly.open("a", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            for month in range(1, 13):
                writer.writerow([f"{year:04d}-{month:02d}", year, month, 60, 10, 20, 30])
        with self.offense.open("a", encoding="utf-8", newline="") as file:
            csv.writer(file).writerow(
                [year, 1, 2, 3, 4, 700, 5, 5, 720, f"Synthetic {year} fixture."]
            )

    @staticmethod
    def read_assignment(text, name):
        prefix = f"window.{name} = "
        line = next(line for line in text.splitlines() if line.startswith(prefix))
        return json.loads(line[len(prefix):-1])

    def test_complete_2026_2027_inputs_update_both_mirrors_identically(self):
        self.append_year(2026)
        self.append_year(2027)

        summary = updater.update_dashboard_data(
            self.monthly, self.offense, self.dashboard, self.docs
        )

        self.assertEqual(
            summary,
            {"start": "2017-01", "end": "2027-12", "months": 132, "years": 11},
        )
        dashboard_text = self.dashboard.read_text(encoding="utf-8")
        self.assertEqual(dashboard_text, self.docs.read_text(encoding="utf-8"))
        monthly = self.read_assignment(dashboard_text, "MONTHLY_DATA")
        offense = self.read_assignment(dashboard_text, "OFFENSE_DATA")
        self.assertEqual(monthly[-1]["date"], "2027-12")
        self.assertEqual(offense[-1]["year"], 2027)
        self.assertEqual(offense[-1]["source_note"], "Synthetic 2027 fixture.")

    def test_invalid_future_input_preserves_both_existing_outputs(self):
        self.dashboard.parent.mkdir()
        self.docs.parent.mkdir()
        self.dashboard.write_text("dashboard sentinel", encoding="utf-8")
        self.docs.write_text("docs sentinel", encoding="utf-8")
        self.append_year(2026)
        lines = self.monthly.read_text(encoding="utf-8-sig").splitlines()
        self.monthly.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8-sig")

        with self.assertRaisesRegex(ValueError, "12월"):
            updater.update_dashboard_data(
                self.monthly, self.offense, self.dashboard, self.docs
            )

        self.assertEqual(self.dashboard.read_text(encoding="utf-8"), "dashboard sentinel")
        self.assertEqual(self.docs.read_text(encoding="utf-8"), "docs sentinel")

    def test_check_mode_never_rewrites_and_detects_stale_output(self):
        updater.update_dashboard_data(
            self.monthly, self.offense, self.dashboard, self.docs
        )
        before = (self.dashboard.stat().st_mtime_ns, self.docs.stat().st_mtime_ns)
        updater.update_dashboard_data(
            self.monthly, self.offense, self.dashboard, self.docs, check=True
        )
        self.assertEqual(
            before, (self.dashboard.stat().st_mtime_ns, self.docs.stat().st_mtime_ns)
        )
        self.docs.write_text("stale", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "갱신이 필요한 출력"):
            updater.update_dashboard_data(
                self.monthly, self.offense, self.dashboard, self.docs, check=True
            )
        self.assertEqual(self.docs.read_text(encoding="utf-8"), "stale")

    def test_second_replace_failure_restores_first_output(self):
        self.dashboard.parent.mkdir()
        self.docs.parent.mkdir()
        self.dashboard.write_text("dashboard original\n", encoding="utf-8")
        self.docs.write_text("docs original\n", encoding="utf-8")
        original_dashboard = self.dashboard.read_bytes()
        original_docs = self.docs.read_bytes()
        real_replace = updater.os.replace
        calls = 0

        def fail_second_replace(source, destination):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("simulated second output failure")
            return real_replace(source, destination)

        with patch.object(updater.os, "replace", side_effect=fail_second_replace):
            with self.assertRaisesRegex(OSError, "second output failure"):
                updater.update_dashboard_data(
                    self.monthly, self.offense, self.dashboard, self.docs
                )

        self.assertEqual(self.dashboard.read_bytes(), original_dashboard)
        self.assertEqual(self.docs.read_bytes(), original_docs)

    def test_cli_check_succeeds_for_repository_mirrors(self):
        result = subprocess.run(
            [sys.executable, "-B", "-X", "utf8", "update_dashboard_data.py", "--check"],
            cwd=analysis.BASE_DIR,
            capture_output=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("2017-01 ~ 2025-12", result.stdout)
        self.assertIn("108개월", result.stdout)


if __name__ == "__main__":
    unittest.main()
