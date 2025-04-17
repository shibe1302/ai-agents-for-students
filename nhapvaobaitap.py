import argparse
import sys
from exercise_handler import import_exercise_from_file, create_tables_if_not_exist


def main():
    """Command-line utility for importing exercises into the database"""
    parser = argparse.ArgumentParser(description='Import C++ exercises from file')
    parser.add_argument('file', help='Path to exercise file (CSV or JSON format)')
    args = parser.parse_args()

    # Initialize database if needed
    create_tables_if_not_exist()

    # Import the exercise
    success, message = import_exercise_from_file(args.file)
    print(message)

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()