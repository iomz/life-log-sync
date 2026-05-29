from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from life_log_sync.config import load_config
from life_log_sync.sources.withings import normalize_measure_groups, write_measures


class WithingsTest(unittest.TestCase):
    def test_normalizes_measure_groups(self) -> None:
        rows = normalize_measure_groups(
            [
                {
                    "grpid": 123,
                    "date": 1780041600,
                    "measures": [
                        {"type": 1, "value": 7050, "unit": -2},
                        {"type": 6, "value": 1842, "unit": -2},
                    ],
                }
            ]
        )

        self.assertEqual(rows[0]["grpid"], 123)
        self.assertEqual(rows[0]["type_name"], "weight")
        self.assertEqual(rows[0]["value"], "70.50")
        self.assertEqual(rows[1]["type_name"], "fat_ratio")
        self.assertEqual(rows[1]["unit"], "%")

    def test_writes_raw_json_and_csv_to_data_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            data_dir = root / "app-data"
            config_path = root / "life-log-sync.toml"
            config_path.write_text(
                f"""
[app]
data_dir = "{data_dir}"

[withings]
access_token = "access"
""".strip(),
                encoding="utf-8",
            )
            config = load_config(config_path)

            written = write_measures(
                config,
                {
                    "measuregrps": [
                        {
                            "grpid": 123,
                            "date": 1780041600,
                            "measures": [{"type": 1, "value": 7050, "unit": -2}],
                        }
                    ]
                },
            )

            raw_path = data_dir / "withings/raw/body_measures.json"
            csv_path = data_dir / "withings/body_measures.csv"
            self.assertIn(raw_path, written)
            self.assertIn(csv_path, written)
            self.assertEqual(json.loads(raw_path.read_text(encoding="utf-8"))["measuregrps"][0]["grpid"], 123)
            with csv_path.open(encoding="utf-8", newline="") as csv_file:
                rows = list(csv.DictReader(csv_file))
            self.assertEqual(rows[0]["type_name"], "weight")


if __name__ == "__main__":
    unittest.main()
