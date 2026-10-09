"""Tests for the vaccination drive SQL scripts, run against a fresh in-memory SQLite database."""
import io
import os
import sqlite3
import unittest
from contextlib import redirect_stdout

import run_sql

SETUP = os.path.join(run_sql.SQL_DIR, "01_setup.sql")
FIX = os.path.join(run_sql.SQL_DIR, "02_verify_and_fix.sql")
REPORTS = os.path.join(run_sql.SQL_DIR, "03_reports.sql")


class SetupScriptTests(unittest.TestCase):
    def setUp(self):
        self.db = run_sql.connect()
        run_sql.run_script(self.db, SETUP)

    def tearDown(self):
        self.db.close()

    def test_two_clinics_with_ids_one_and_two(self):
        rows = self.db.execute("SELECT id, name, location FROM clinics ORDER BY id").fetchall()
        self.assertEqual(rows, [(1, "Downtown Center", "Main St"), (2, "Westside Clinic", "Oak Ave")])

    def test_three_vaccinations_inserted(self):
        rows = self.db.execute("SELECT * FROM vaccinations ORDER BY id").fetchall()
        self.assertEqual(rows, [
            (1, "Emma Wilson", "emma@example.com", 1, "Pfizer", "2025-01-10", 1),
            (2, "Liam Brown", "liam@example.com", 1, "Moderna", "2025-01-11", 2),
            (3, "Olivia Davis", "olivia@example.com", 2, "Pfizer", "2025-01-12", 1),
        ])

    def test_vaccinations_has_the_seven_required_columns(self):
        columns = [row[1] for row in self.db.execute("PRAGMA table_info(vaccinations)")]
        self.assertEqual(columns, ["id", "patient_name", "patient_email", "dose_number",
                                   "vaccine_type", "vaccination_date", "clinic_id"])

    def test_setup_can_be_run_again_without_errors(self):
        run_sql.run_script(self.db, FIX)
        run_sql.run_script(self.db, SETUP)
        count = self.db.execute("SELECT COUNT(*) FROM vaccinations").fetchone()[0]
        self.assertEqual(count, 3)

    def test_clinic_id_must_point_at_a_real_clinic(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO vaccinations (patient_name, patient_email, dose_number, "
                            "vaccine_type, vaccination_date, clinic_id) "
                            "VALUES ('Test', 't@example.com', 1, 'Pfizer', '2025-01-13', 99)")

    def test_dropping_clinics_first_fails_once_vaccinations_exist(self):
        # This is why 01_setup.sql drops vaccinations before clinics.
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("DROP TABLE clinics")


class VerifyAndFixScriptTests(unittest.TestCase):
    def setUp(self):
        self.db = run_sql.connect()
        run_sql.run_script(self.db, SETUP)
        self.results = run_sql.run_script(self.db, FIX)

    def tearDown(self):
        self.db.close()

    def test_first_select_shows_all_three_rows_before_changes(self):
        columns, rows = self.results[0]
        self.assertEqual(columns[0], "id")
        self.assertEqual(len(columns), 7)
        self.assertEqual([row[1] for row in rows], ["Emma Wilson", "Liam Brown", "Olivia Davis"])
        self.assertEqual(rows[1][4], "Moderna")

    def test_liam_is_updated_to_pfizer(self):
        vaccine = self.db.execute(
            "SELECT vaccine_type FROM vaccinations WHERE patient_name = 'Liam Brown'").fetchone()[0]
        self.assertEqual(vaccine, "Pfizer")

    def test_update_touches_only_liam(self):
        emma = self.db.execute(
            "SELECT vaccine_type, dose_number FROM vaccinations WHERE patient_name = 'Emma Wilson'").fetchone()
        self.assertEqual(emma, ("Pfizer", 1))

    def test_update_and_delete_leave_other_patients_alone(self):
        # A Moderna patient who is not Liam must stay Moderna; without a WHERE clause they would not.
        db = run_sql.connect()
        run_sql.run_script(db, SETUP)
        db.execute("INSERT INTO vaccinations VALUES (4, 'Noah Lee', 'noah@example.com', 1, "
                   "'Moderna', '2025-01-13', 2)")
        run_sql.run_script(db, FIX)
        rows = db.execute("SELECT patient_name, vaccine_type FROM vaccinations ORDER BY id").fetchall()
        db.close()
        self.assertEqual(rows, [("Emma Wilson", "Pfizer"), ("Liam Brown", "Pfizer"),
                                ("Noah Lee", "Moderna")])

    def test_olivia_is_deleted_and_two_rows_remain(self):
        names = [row[0] for row in self.db.execute("SELECT patient_name FROM vaccinations ORDER BY id")]
        self.assertEqual(names, ["Emma Wilson", "Liam Brown"])

    def test_second_select_shows_the_corrected_table(self):
        _, rows = self.results[1]
        self.assertEqual([(row[1], row[4]) for row in rows],
                         [("Emma Wilson", "Pfizer"), ("Liam Brown", "Pfizer")])


class ReportScriptTests(unittest.TestCase):
    def setUp(self):
        self.db = run_sql.connect()
        run_sql.run_script(self.db, SETUP)
        run_sql.run_script(self.db, FIX)
        self.results = run_sql.run_script(self.db, REPORTS)

    def tearDown(self):
        self.db.close()

    def test_reports_script_returns_two_result_sets(self):
        self.assertEqual(len(self.results), 2)

    def test_inner_join_shows_patient_vaccine_and_clinic_name(self):
        columns, rows = self.results[0]
        self.assertEqual(columns, ["patient_name", "vaccine_type", "clinic_name"])
        self.assertEqual(rows, [("Emma Wilson", "Pfizer", "Downtown Center"),
                                ("Liam Brown", "Pfizer", "Westside Clinic")])

    def test_group_by_gives_one_row_per_clinic(self):
        columns, rows = self.results[1]
        self.assertEqual(columns, ["clinic_name", "vaccination_count"])
        self.assertEqual(rows, [("Downtown Center", 1), ("Westside Clinic", 1)])

    def test_count_before_the_delete_includes_olivia(self):
        db = run_sql.connect()
        run_sql.run_script(db, SETUP)
        _, rows = run_sql.run_script(db, REPORTS)[1]
        db.close()
        self.assertEqual(rows, [("Downtown Center", 2), ("Westside Clinic", 1)])


class SplitStatementTests(unittest.TestCase):
    def test_windows_line_endings_are_handled(self):
        text = "-- note\r\nSELECT 1;\r\nSELECT 2;\r\n"
        self.assertEqual(run_sql.split_statements(text), ["-- note\nSELECT 1;", "SELECT 2;"])

    def test_semicolon_inside_quotes_does_not_split(self):
        text = "INSERT INTO t VALUES ('a;b');\nSELECT 1;\n"
        self.assertEqual(len(run_sql.split_statements(text)), 2)

    def test_trailing_comment_is_ignored(self):
        self.assertEqual(run_sql.split_statements("SELECT 1;\n-- the end\n"), ["SELECT 1;"])

    def test_missing_semicolon_is_reported(self):
        with self.assertRaises(ValueError):
            run_sql.split_statements("SELECT 1;\nSELECT 2\n")


class MainTests(unittest.TestCase):
    def test_main_runs_all_scripts_and_prints_the_clinic_count(self):
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = run_sql.main(run_sql.SCRIPT_ORDER)
        self.assertEqual(exit_code, 0)
        self.assertIn("Downtown Center | 1", output.getvalue())
        self.assertIn("Westside Clinic | 1", output.getvalue())

    def test_main_reports_a_missing_file_with_exit_code_one(self):
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = run_sql.main(["99_missing.sql"])
        self.assertEqual(exit_code, 1)
        self.assertIn("ERROR:", output.getvalue())


if __name__ == "__main__":
    unittest.main()