import sqlite3
import sys
from pathlib import Path

from src.db.init_db import DB_PATH
from src.ingest.matches import ImportValidationError, import_matches_csv


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python -m src.ingest.import_matches path/to/matches.csv")
        sys.exit(1)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            result = import_matches_csv(conn, Path(sys.argv[1]))
        except ImportValidationError as e:
            print("Import failed, nothing was written:\n" + str(e))
            sys.exit(1)
    print(result)


if __name__ == "__main__":
    main()
