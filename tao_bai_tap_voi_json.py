import json

def create_exercise_json(title, difficulty, description, test_cases, filename="exercise_data.json"):
    """
    Creates a JSON data file containing exercise information.

    Args:
        title (str): The title of the exercise.
        difficulty (str): The difficulty level of the exercise (e.g., "Easy", "Medium", "Hard").
        description (str): A description of the exercise.
        test_cases (list): A list of dictionaries, where each dictionary represents a test case
                           with "input", "expected_output", and "is_hidden" keys.
        filename (str, optional): The name of the JSON file to create.
                                   Defaults to "exercise_data.json".
    """
    exercise_data = {
        "title": title,
        "difficulty": difficulty,
        "description": description,
        "test_cases": test_cases
    }

    try:
        with open(filename, 'w',encoding='utf-8') as json_file:
            json.dump(exercise_data, json_file, indent=2)  # Use indent for better readability
        print(f"JSON data successfully written to '{filename}'")
    except IOError as e:
        print(f"Error writing to file '{filename}': {e}")

if __name__ == "__main__":
    # Example usage:
    exercise_title = "Sum of Two Numbers"
    exercise_difficulty = "Easy"
    exercise_description = "Write a function that takes two integers as input and returns their sum."
    exercise_test_cases = [
        {"input": "5 10", "expected_output": "15", "is_hidden": False},
        {"input": "-3 8", "expected_output": "5", "is_hidden": False},
        {"input": "0 0", "expected_output": "0", "is_hidden": True},
        {"input": "100 -50", "expected_output": "50", "is_hidden": True}
    ]

    create_exercise_json(exercise_title, exercise_difficulty, exercise_description, exercise_test_cases)
    # You can also specify a different filename:
    # create_exercise_json(exercise_title, exercise_difficulty, exercise_description, exercise_test_cases, "math_exercise.json")