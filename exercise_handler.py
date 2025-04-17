import sqlite3
import os
import subprocess
import tempfile
import json
import uuid
from datetime import datetime

# Database path
DB_PATH = "dataBase/exercises.db"


def create_tables_if_not_exist():
    """Initialize the exercises database with necessary tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create exercises table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS exercises (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create test cases table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS test_cases (
        id INTEGER PRIMARY KEY,
        exercise_id INTEGER NOT NULL,
        input TEXT,
        expected_output TEXT NOT NULL,
        is_hidden BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (exercise_id) REFERENCES exercises(id)
    )
    ''')

    # Create submissions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS submissions (
        id TEXT PRIMARY KEY,
        exercise_id INTEGER NOT NULL,
        code TEXT NOT NULL,
        passed BOOLEAN NOT NULL,
        feedback TEXT,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (exercise_id) REFERENCES exercises(id)
    )
    ''')

    # Create user progress table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_progress (
        exercise_id INTEGER PRIMARY KEY,
        completed BOOLEAN DEFAULT FALSE,
        completed_at TIMESTAMP,
        FOREIGN KEY (exercise_id) REFERENCES exercises(id)
    )
    ''')

    # Insert sample exercises if none exist
    cursor.execute("SELECT COUNT(*) FROM exercises")
    if cursor.fetchone()[0] == 0:
        _insert_sample_exercises(cursor)

    conn.commit()
    conn.close()


def _insert_sample_exercises(cursor):
    """Insert sample C++ exercises into the database"""
    # Exercise 1: Hello World
    cursor.execute(
        "INSERT INTO exercises (title, description, difficulty) VALUES (?, ?, ?)",
        (
            "Hello World",
            """# Hello World in C++

Write a C++ program that prints "Hello, World!" to the console.

Your program should:
1. Include the necessary header for console output
2. Use the standard namespace
3. Define a main function that returns 0
4. Print exactly "Hello, World!" (without quotes) to the console
            """,
            "Easy"
        )
    )
    ex1_id = cursor.lastrowid

    # Test cases for Exercise 1
    cursor.execute(
        "INSERT INTO test_cases (exercise_id, input, expected_output, is_hidden) VALUES (?, ?, ?, ?)",
        (ex1_id, "", "Hello, World!", False)
    )

    # Exercise 2: Sum of Two Numbers
    cursor.execute(
        "INSERT INTO exercises (title, description, difficulty) VALUES (?, ?, ?)",
        (
            "Sum of Two Numbers",
            """# Sum of Two Numbers

Write a C++ program that reads two integers from the user and prints their sum.

Requirements:
1. Include the necessary headers
2. Use the standard namespace
3. Read two integers from standard input
4. Calculate their sum
5. Print the result in the format "Sum: X" (where X is the sum)
            """,
            "Easy"
        )
    )
    ex2_id = cursor.lastrowid

    # Test cases for Exercise 2
    cursor.execute(
        "INSERT INTO test_cases (exercise_id, input, expected_output, is_hidden) VALUES (?, ?, ?, ?)",
        (ex2_id, "5\n7", "Sum: 12", False)
    )
    cursor.execute(
        "INSERT INTO test_cases (exercise_id, input, expected_output, is_hidden) VALUES (?, ?, ?, ?)",
        (ex2_id, "10\n20", "Sum: 30", False)
    )
    cursor.execute(
        "INSERT INTO test_cases (exercise_id, input, expected_output, is_hidden) VALUES (?, ?, ?, ?)",
        (ex2_id, "-5\n10", "Sum: 5", True)
    )






def get_all_exercises():
    """Return a list of all exercises"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, difficulty FROM exercises ORDER BY id")
    exercises = cursor.fetchall()
    conn.close()
    return exercises


def get_exercise_details(exercise_id):
    """Get details for a specific exercise"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get exercise details
    cursor.execute("SELECT title, description, difficulty FROM exercises WHERE id = ?", (exercise_id,))
    result = cursor.fetchone()

    if not result:
        conn.close()
        return None

    title, description, difficulty = result

    # Get non-hidden test cases
    cursor.execute("SELECT input, expected_output FROM test_cases WHERE exercise_id = ? AND is_hidden = 0",
                   (exercise_id,))
    test_cases = cursor.fetchall()

    conn.close()

    return {
        'title': title,
        'description': description,
        'difficulty': difficulty,
        'test_cases': test_cases
    }


def save_submission(exercise_id, code, results):
    """Save a code submission to the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    submission_id = str(uuid.uuid4())
    passed = results['passed_tests'] == results['total_tests']

    cursor.execute(
        "INSERT INTO submissions (id, exercise_id, code, passed, feedback) VALUES (?, ?, ?, ?, ?)",
        (submission_id, exercise_id, code, passed, results['feedback'])
    )

    # Update user progress if all tests passed
    if passed:
        cursor.execute(
            "INSERT OR REPLACE INTO user_progress (exercise_id, completed, completed_at) VALUES (?, ?, ?)",
            (exercise_id, True, datetime.now().isoformat())
        )

    conn.commit()
    conn.close()

    return submission_id


def check_submission(exercise_id, file_path):
    """Check a C++ submission against test cases using Docker"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all test cases for the exercise
    cursor.execute("SELECT id, input, expected_output, is_hidden FROM test_cases WHERE exercise_id = ?", (exercise_id,))
    test_cases = cursor.fetchall()

    conn.close()

    results = {
        'passed_tests': 0,
        'total_tests': len(test_cases),
        'details': [],
        'feedback': ''
    }

    # Compile the code (Replace this with Docker execution in production)
    # For now, we'll simulate compilation and execution for demonstration
    try:
        # Compile (in a real scenario, this would be done in Docker)
        compile_output = subprocess.run(['g++', file_path, '-o', f"{file_path}.out"],
                                        capture_output=True, text=True)

        if compile_output.returncode != 0:
            # Compilation error
            results['feedback'] = f"Compilation Error:\n{compile_output.stderr}"
            return results

        # For each test case
        for test_id, test_input, expected_output, is_hidden in test_cases:
            # Create temporary input file
            with tempfile.NamedTemporaryFile('w', delete=False) as input_file:
                input_file.write(test_input)
                input_path = input_file.name

            # Run the compiled program
            try:
                with open(input_path, 'r') as stdin:
                    process = subprocess.run([f"{file_path}.out"],
                                             stdin=stdin,
                                             capture_output=True,
                                             text=True,
                                             timeout=5)  # 5 second timeout

                # Get output and strip whitespace
                actual_output = process.stdout.strip()
                expected_output = expected_output.strip()

                # Check if output matches expected
                passed = actual_output == expected_output

                if passed:
                    results['passed_tests'] += 1

                # Add test case details
                test_result = {
                    'test_id': test_id,
                    'passed': passed,
                    'input': test_input if not is_hidden else "[Hidden]",
                    'expected': expected_output if not is_hidden else "[Hidden]",
                    'actual': actual_output if not is_hidden else "[Hidden]"
                }

                results['details'].append(test_result)

            except subprocess.TimeoutExpired:
                results['details'].append({
                    'test_id': test_id,
                    'passed': False,
                    'input': test_input if not is_hidden else "[Hidden]",
                    'expected': expected_output if not is_hidden else "[Hidden]",
                    'actual': "Timeout - Program took too long to execute"
                })

            # Clean up input file
            os.unlink(input_path)

        # Generate feedback
        feedback = []
        feedback.append(f"Test Results: {results['passed_tests']}/{results['total_tests']} passed\n")

        for i, test in enumerate(results['details']):
            status = "✅ Passed" if test['passed'] else "❌ Failed"
            feedback.append(f"Test {i + 1}: {status}")

            if not test['passed']:
                feedback.append(f"  Input: {test['input']}")
                feedback.append(f"  Expected: {test['expected']}")
                feedback.append(f"  Your output: {test['actual']}")
                feedback.append("")

        results['feedback'] = "\n".join(feedback)

    except Exception as e:
        results['feedback'] = f"Error: {str(e)}"

    # Clean up compiled file
    try:
        os.unlink(f"{file_path}.out")
    except:
        pass

    return results


def get_user_progress():
    """Get the number of completed exercises"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM user_progress WHERE completed = 1")
    count = cursor.fetchone()[0]

    conn.close()
    return count


def import_exercise_from_file(file_path):
    """Import exercise data from a CSV or text file"""
    try:
        with open(file_path, 'r') as f:
            data = f.read().strip()

        lines = data.split('\n')

        # Check if the file is in CSV format
        if ',' in lines[0]:
            # Process as CSV
            title = lines[0].split(',')[0].strip()
            difficulty = lines[0].split(',')[1].strip()
            description = '\n'.join(lines[1:lines.index("TEST CASES")])
            test_case_lines = lines[lines.index("TEST CASES") + 1:]

            test_cases = []
            current_input = []
            current_output = []
            is_input = True

            for line in test_case_lines:
                if line == "INPUT:":
                    if current_input and current_output:
                        test_cases.append({
                            'input': '\n'.join(current_input),
                            'expected_output': '\n'.join(current_output),
                            'is_hidden': False
                        })
                        current_input = []
                        current_output = []
                    is_input = True
                elif line == "OUTPUT:":
                    is_input = False
                elif line.startswith("HIDDEN:"):
                    if current_input and current_output:
                        test_cases.append({
                            'input': '\n'.join(current_input),
                            'expected_output': '\n'.join(current_output),
                            'is_hidden': True
                        })
                        current_input = []
                        current_output = []
                    is_input = True
                else:
                    if is_input:
                        current_input.append(line)
                    else:
                        current_output.append(line)

            # Add the last test case if any
            if current_input and current_output:
                test_cases.append({
                    'input': '\n'.join(current_input),
                    'expected_output': '\n'.join(current_output),
                    'is_hidden': False
                })
        else:
            # Process as JSON-like format
            data_dict = json.loads(data)
            title = data_dict.get('title', 'Untitled Exercise')
            difficulty = data_dict.get('difficulty', 'Medium')
            description = data_dict.get('description', '')
            test_cases = data_dict.get('test_cases', [])

        # Save to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO exercises (title, description, difficulty) VALUES (?, ?, ?)",
            (title, description, difficulty)
        )

        exercise_id = cursor.lastrowid

        for tc in test_cases:
            cursor.execute(
                "INSERT INTO test_cases (exercise_id, input, expected_output, is_hidden) VALUES (?, ?, ?, ?)",
                (exercise_id, tc['input'], tc['expected_output'], tc.get('is_hidden', False))
            )

        conn.commit()
        conn.close()

        return True, f"Exercise '{title}' imported successfully with ID {exercise_id}"

    except Exception as e:
        return False, f"Error importing exercise: {str(e)}"