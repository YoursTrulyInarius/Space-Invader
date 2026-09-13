"""Create the configured Space Invaders database and schema."""
import sys

from database import Database


def main():
    database = Database()
    try:
        if not database.connected:
            print("Database setup failed. Check MySQL and config.py.")
            return 1

        if not database.initialize_schema():
            print("Database setup failed while creating the schema.")
            return 1

        print(f"Database setup complete: {database.database}")
        return 0
    finally:
        database.close()


if __name__ == '__main__':
    sys.exit(main())