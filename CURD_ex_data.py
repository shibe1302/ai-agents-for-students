import sqlite3
from datetime import datetime

# Database path (same as in exercise_handler.py)
DB_PATH = "dataBase/exercises.db"


def connect_db():
    """Create a connection to the database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn


def create_exercise(title, description, difficulty, test_cases):
    """
    Create a new exercise with test cases

    Args:
        title (str): Exercise title
        description (str): Exercise description
        difficulty (str): Exercise difficulty level
        test_cases (list): List of dictionaries with keys 'input', 'expected_output', and 'is_hidden'

    Returns:
        tuple: (success bool, message string)
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Insert exercise
        cursor.execute(
            "INSERT INTO exercises (title, description, difficulty) VALUES (?, ?, ?)",
            (title, description, difficulty)
        )

        exercise_id = cursor.lastrowid

        # Insert test cases
        for tc in test_cases:
            cursor.execute(
                "INSERT INTO test_cases (exercise_id, input, expected_output, is_hidden) VALUES (?, ?, ?, ?)",
                (exercise_id, tc.get('input', ''), tc['expected_output'], tc.get('is_hidden', False))
            )

        conn.commit()
        conn.close()

        return True, f"Exercise '{title}' created successfully with ID {exercise_id}"

    except Exception as e:
        return False, f"Error creating exercise: {str(e)}"


def read_exercise(exercise_id):
    """
    Get details of an exercise including test cases

    Args:
        exercise_id (int): Exercise ID

    Returns:
        dict: Exercise details or None if not found
    """
    conn = connect_db()
    cursor = conn.cursor()

    # Get exercise details
    cursor.execute("SELECT * FROM exercises WHERE id = ?", (exercise_id,))
    exercise = cursor.fetchone()

    if not exercise:
        conn.close()
        return None

    # Convert to dictionary
    exercise_dict = dict(exercise)

    # Get all test cases
    cursor.execute("SELECT * FROM test_cases WHERE exercise_id = ?", (exercise_id,))
    test_cases = [dict(tc) for tc in cursor.fetchall()]

    exercise_dict['test_cases'] = test_cases

    conn.close()
    return exercise_dict


def update_exercise(exercise_id, title=None, description=None, difficulty=None):
    """
    Update an existing exercise

    Args:
        exercise_id (int): Exercise ID
        title (str, optional): New title
        description (str, optional): New description
        difficulty (str, optional): New difficulty level

    Returns:
        tuple: (success bool, message string)
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Check if exercise exists
        cursor.execute("SELECT id FROM exercises WHERE id = ?", (exercise_id,))
        if not cursor.fetchone():
            conn.close()
            return False, f"Exercise with ID {exercise_id} not found"

        # Build update query
        update_fields = []
        params = []

        if title is not None:
            update_fields.append("title = ?")
            params.append(title)

        if description is not None:
            update_fields.append("description = ?")
            params.append(description)

        if difficulty is not None:
            update_fields.append("difficulty = ?")
            params.append(difficulty)

        if not update_fields:
            conn.close()
            return False, "No fields provided for update"

        # Execute update
        query = f"UPDATE exercises SET {', '.join(update_fields)} WHERE id = ?"
        params.append(exercise_id)

        cursor.execute(query, params)
        conn.commit()
        conn.close()

        return True, f"Exercise with ID {exercise_id} updated successfully"

    except Exception as e:
        return False, f"Error updating exercise: {str(e)}"


def delete_exercise(exercise_id):
    """
    Delete an exercise and all related records

    Args:
        exercise_id (int): Exercise ID

    Returns:
        tuple: (success bool, message string)
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Check if exercise exists
        cursor.execute("SELECT id FROM exercises WHERE id = ?", (exercise_id,))
        if not cursor.fetchone():
            conn.close()
            return False, f"Exercise with ID {exercise_id} not found"

        # Begin transaction
        conn.execute("BEGIN TRANSACTION")

        # Delete related records from user_progress
        cursor.execute("DELETE FROM user_progress WHERE exercise_id = ?", (exercise_id,))

        # Delete related records from submissions
        cursor.execute("DELETE FROM submissions WHERE exercise_id = ?", (exercise_id,))

        # Delete related records from test_cases
        cursor.execute("DELETE FROM test_cases WHERE exercise_id = ?", (exercise_id,))

        # Delete the exercise
        cursor.execute("DELETE FROM exercises WHERE id = ?", (exercise_id,))

        # Commit transaction
        conn.commit()
        conn.close()

        return True, f"Exercise with ID {exercise_id} and all related data deleted successfully"

    except Exception as e:
        # Roll back any changes if an error occurs
        if conn:
            conn.rollback()
            conn.close()
        return False, f"Error deleting exercise: {str(e)}"


def add_test_case(exercise_id, input_data, expected_output, is_hidden=False):
    """
    Add a test case to an existing exercise

    Args:
        exercise_id (int): Exercise ID
        input_data (str): Test case input
        expected_output (str): Expected output
        is_hidden (bool): Whether the test case is hidden

    Returns:
        tuple: (success bool, message string)
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Check if exercise exists
        cursor.execute("SELECT id FROM exercises WHERE id = ?", (exercise_id,))
        if not cursor.fetchone():
            conn.close()
            return False, f"Exercise with ID {exercise_id} not found"

        # Insert test case
        cursor.execute(
            "INSERT INTO test_cases (exercise_id, input, expected_output, is_hidden) VALUES (?, ?, ?, ?)",
            (exercise_id, input_data, expected_output, is_hidden)
        )

        test_case_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return True, f"Test case added successfully with ID {test_case_id}"

    except Exception as e:
        return False, f"Error adding test case: {str(e)}"


def delete_test_case(test_case_id):
    """
    Delete a test case

    Args:
        test_case_id (int): Test case ID

    Returns:
        tuple: (success bool, message string)
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Check if test case exists
        cursor.execute("SELECT id FROM test_cases WHERE id = ?", (test_case_id,))
        if not cursor.fetchone():
            conn.close()
            return False, f"Test case with ID {test_case_id} not found"

        # Delete test case
        cursor.execute("DELETE FROM test_cases WHERE id = ?", (test_case_id,))

        conn.commit()
        conn.close()

        return True, f"Test case with ID {test_case_id} deleted successfully"

    except Exception as e:
        return False, f"Error deleting test case: {str(e)}"


def list_exercises(difficulty=None):
    """
    List all exercises with optional filtering by difficulty

    Args:
        difficulty (str, optional): Filter by difficulty level

    Returns:
        list: List of exercise dictionaries
    """
    conn = connect_db()
    cursor = conn.cursor()

    if difficulty:
        cursor.execute("SELECT * FROM exercises WHERE difficulty = ? ORDER BY id", (difficulty,))
    else:
        cursor.execute("SELECT * FROM exercises ORDER BY id")

    exercises = [dict(ex) for ex in cursor.fetchall()]
    conn.close()

    return exercises


def get_submission_history(exercise_id):
    """
    Get submission history for an exercise

    Args:
        exercise_id (int): Exercise ID

    Returns:
        list: List of submission dictionaries
    """
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM submissions WHERE exercise_id = ? ORDER BY submitted_at DESC", (exercise_id,))
    submissions = [dict(sub) for sub in cursor.fetchall()]

    conn.close()
    return submissions
# To delete an exercise:
success, message = delete_exercise(exercise_id=3)
if success:
    print(message)  # Exercise with ID 5 and all related data deleted successfully
else:
    print(message)  # Will show error message if deletion failed