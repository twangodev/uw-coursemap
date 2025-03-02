import json
import os


def read_json_file(filepath):
    """
    Reads JSON data from a single file and returns its dictionary representation.

    Parameters:
    - filepath (str): Path to the JSON file.

    Returns:
    - dict: The JSON data as a dictionary, or None if an error occurs.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from file {filepath}: {e}")
    except Exception as e:
        print(f"Error processing file {filepath}: {e}")
    return None

def read_json_directory(directory_path):
    """
    Reads all JSON files in the specified directory and returns a dictionary mapping
    the file name (excluding the '.json' extension) to its dictionary representation.

    Parameters:
    - directory_path (str): Path to the directory containing JSON files.

    Returns:
    - dict: A dictionary with keys as file names (without extension) and values as the JSON data.
    """
    json_data = {}
    # Loop through all files in the given directory
    for filename in os.listdir(directory_path):
        if filename.endswith('.json'):
            filepath = os.path.join(directory_path, filename)
            data = read_json_file(filepath)
            if data is not None:
                # Use the file name without the '.json' extension as the key
                file_key = os.path.splitext(filename)[0]
                json_data[file_key] = data
    return json_data

def get_subjects(data_dir, logger):
    subjects = read_json_file(os.path.join(data_dir, "subjects.json"))

    logger.info(f"Loaded {len(subjects)} subjects.")
    return subjects

def get_instructors(data_dir, logger):
    instructor_dir = os.path.join(data_dir, "instructors")

    instructors = read_json_directory(instructor_dir)
    logger.info(f"Loaded {len(instructors)} instructors.")

    return instructors

def get_courses(data_dir, subjects, logger):
    course_dir = os.path.join(data_dir, "course")

    courses = read_json_directory(course_dir)
    logger.info(f"Loaded {len(courses)} courses.")

    return {
        course_id: {
            "course_reference": process_course_reference(course_data["course_reference"]),
            "course_title": course_data["course_title"],
            "subjects": [subjects[shorthand] for shorthand in course_data["course_reference"]["subjects"]],
        }
        for course_id, course_data in courses.items()
    }

def process_course_reference(course_reference):
    course_number = course_reference["course_number"]
    subjects = sorted(course_reference["subjects"])

    return f"{'/'.join(subjects)} {course_number}"


