"""Run the vaccination drive SQL files against a fresh SQLite database and print every result.

This does from the terminal what DBeaver does when you run a script: it executes
each statement in order and shows the rows any SELECT returns.
"""
import os 
import sqlite3
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SQL_DIR = os.path.join(PROJECT_DIR, "sql")
SCRIPT_ORDER = ["01_setup.sql", "02_verify_and_fix.sql", "03_reports.sql"]


def connect(database=":memory:"):
    """Open a SQLite connection with foreign key checks switched on."""
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

def has_code(text):
    """True if text contains anything other than blank lines and -- comments."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("--"):
            return True
    return False

def split_statements(sql_text):
    """Split a script into single statements, keeping semicolons inside quotes intact."""
    statements = []
    buffer = ""
    for line in sql_text.splitlines():
        buffer += line + "\n"
        if sqlite3.complete_statement(buffer):
            if has_code(buffer):
                statements.append(buffer.strip())
            buffer = ""
    if has_code(buffer):
        raise ValueError("Statement without a closing semicolon: " + buffer.strip())
    return statements
def run_script(connection, path):
    """Run every statement in one file. Returns a list of (columns, rows) for each SELECT."""
    with open(path, encoding="utf-8-sig") as sql_file:
        statements = split_statements(sql_file.read())
    results = []
    for statement in statements:
        cursor = connection.execute(statement)
        if cursor.description is not None:
            columns = [column[0] for column in cursor.description]
            results.append((columns, cursor.fetchall()))
    connection.commit()
    return results

def format_table(columns, rows):
    """Lay out a result set as plain text columns, like DBeaver's results grid."""
    cells = [[str(value) for value in row] for row in rows]
    widths = [len(name) for name in columns]
    for row in cells:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))
    lines = [" | ".join(name.ljust(widths[i]) for i, name in enumerate(columns)).rstrip()]
    lines.append("-+-".join("-" * width for width in widths))
    for row in cells:
        lines.append(" | ".join(value.ljust(widths[i]) for i, value in enumerate(row)).rstrip())
    lines.append("(" + str(len(rows)) + " row" + ("" if len(rows) == 1 else "s") + ")")
    return "\n".join(lines)


def main(file_names):
    connection = connect()
    try:
        for file_name in file_names:
            print("=== " + file_name + " ===")
            results = run_script(connection, os.path.join(SQL_DIR, file_name))
            if not results:
                print("(no result sets)")
            for columns, rows in results:
                print(format_table(columns, rows))
                print()
    except (sqlite3.Error, ValueError, OSError) as error:
        print("ERROR: " + str(error))
        return 1
    finally:
        connection.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or SCRIPT_ORDER))