import json
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from collections import defaultdict
from logging import getLogger

from tqdm import tqdm

from instructors import FullInstructor
from json_serializable import JsonSerializable
from sitemap_generation import generate_sitemap, sanitize_entry

logger = getLogger(__name__)

def chunk_meetings_by_date(meetings, directory_tuple, data_dir):
    """
    Generic function to chunk meetings by date and write them to organized directories.
    
    Args:
        meetings: List of Meeting objects to chunk
        directory_tuple: Tuple of directory components (e.g., ("meetings", "building", "Memorial_Union"))
        data_dir: Base data directory for writing files
    
    Directory structure: {directory_tuple}/MM/DD/YY/meetings.json
    Dates are converted to Central Time, handling daylight savings automatically.
    """
    # Use US/Central timezone which automatically handles DST
    central_tz = ZoneInfo("US/Central")
    
    # Group meetings by date
    date_meetings = defaultdict(list)
    
    for meeting in meetings:
        # Skip meetings without start_time
        if not meeting.start_time:
            continue
            
        # Convert epoch ms to datetime in Central Time
        start_datetime = datetime.fromtimestamp(meeting.start_time / 1000, tz=central_tz)
        
        # Extract date components
        year = start_datetime.strftime("%y")  # 2-digit year
        month = start_datetime.strftime("%m")  # 2-digit month
        day = start_datetime.strftime("%d")    # 2-digit day
        
        # Create date key for grouping meetings on the same day
        date_key = f"{month}/{day}/{year}"
        
        # Add meeting to the appropriate date bucket
        date_meetings[date_key].append(meeting)
    
    # Write meetings to files organized by date
    files_written = 0
    for date_key, meetings_for_date in date_meetings.items():
        # Parse date components for directory structure
        month, day, year = date_key.split("/")
        
        # Build full directory tuple: base_directory + MM/DD/YY
        full_directory_tuple = directory_tuple + (month, day, year)
        write_file(data_dir, full_directory_tuple, "meetings", meetings_for_date)
        files_written += 1
    
    return files_written

def chunk_meetings_by_date_and_building(course_to_meetings, data_dir):
    """
    Chunks meetings by date and building, writing them to organized directories.
    
    Args:
        course_to_meetings: Dict mapping course identifiers to lists of Meeting objects
        data_dir: Base data directory for writing files
    
    Directory structure: /meetings/building/{building_name}/MM/DD/YY/meetings.json
    Dates are converted to Central Time, handling daylight savings automatically.
    """
    # Group meetings by building
    building_meetings = defaultdict(list)
    
    # Flatten all meetings from all courses and group by building
    all_meetings = []
    for course_identifier, meetings in course_to_meetings.items():
        if meetings:
            all_meetings.extend(meetings)
    
    logger.info(f"Processing {len(all_meetings)} total meetings for date/building chunking")
    
    for meeting in all_meetings:
        # Skip meetings without location
        if not meeting.location or not meeting.start_time:
            continue
            
        # Use building name from location
        building_name = meeting.location.building
        if not building_name:
            building_name = "Unknown_Building"
        
        # Add meeting to the appropriate building bucket
        building_meetings[building_name].append(meeting)
    
    # Write meetings for each building using the generic chunking function
    total_files_written = 0
    for building_name, meetings in tqdm(building_meetings.items(), desc="Writing meeting files by building", unit="building"):
        directory_tuple = ("meetings", "building", building_name)
        files_written = chunk_meetings_by_date(meetings, directory_tuple, data_dir)
        total_files_written += files_written
    
    logger.info(f"Wrote {total_files_written} meeting files organized by building and date")
    logger.info(f"Meetings organized across {len(building_meetings)} buildings")

def chunk_meetings_by_date_and_instructor(course_to_meetings, data_dir):
    """
    Chunks meetings by instructor and date.
    
    Directory structure: /meetings/instructor/{instructor_name}/MM/DD/YY/meetings.json
    """
    # Group meetings by instructor
    instructor_meetings = defaultdict(list)
    
    # Flatten all meetings from all courses and group by instructor
    all_meetings = []
    for course_identifier, meetings in course_to_meetings.items():
        if meetings:
            all_meetings.extend(meetings)
    
    logger.info(f"Processing {len(all_meetings)} total meetings for date/instructor chunking")
    
    for meeting in all_meetings:
        # Skip meetings without start_time or instructors
        if not meeting.start_time or not meeting.instructors:
            continue
            
        # Add meeting to each instructor's bucket (meetings can have multiple instructors)
        for instructor_name in meeting.instructors:
            instructor_meetings[instructor_name].append(meeting)
    
    # Write meetings for each instructor using the generic chunking function
    total_files_written = 0
    for instructor_name, meetings in tqdm(instructor_meetings.items(), desc="Writing meeting files by instructor", unit="instructor"):
        directory_tuple = ("meetings", "instructor", instructor_name)
        files_written = chunk_meetings_by_date(meetings, directory_tuple, data_dir)
        total_files_written += files_written
    
    logger.info(f"Wrote {total_files_written} meeting files organized by instructor and date")
    logger.info(f"Meetings organized across {len(instructor_meetings)} instructors")

def chunk_meetings_by_date_and_subject(course_to_meetings, data_dir):
    """
    Example function showing how to chunk meetings by subject.
    
    Directory structure: /meetings/subject/{subject_code}/MM/DD/YY/meetings.json
    """
    # Group meetings by subject (derived from course identifier)
    subject_meetings = defaultdict(list)
    
    logger.info(f"Processing {len(course_to_meetings)} courses for date/subject chunking")
    
    for course_identifier, meetings in course_to_meetings.items():
        if not meetings:
            continue
            
        # Extract subject from course identifier (assuming format like "CS-540")
        subject_code = course_identifier.split("-")[0] if "-" in course_identifier else "Unknown_Subject"
        
        # Add all meetings for this course to the subject bucket
        subject_meetings[subject_code].extend(meetings)
    
    # Write meetings for each subject using the generic chunking function
    total_files_written = 0
    for subject_code, meetings in tqdm(subject_meetings.items(), desc="Writing meeting files by subject", unit="subject"):
        directory_tuple = ("meetings", "subject", subject_code)
        files_written = chunk_meetings_by_date(meetings, directory_tuple, data_dir)
        total_files_written += files_written
    
    logger.info(f"Wrote {total_files_written} meeting files organized by subject and date")
    logger.info(f"Meetings organized across {len(subject_meetings)} subjects")

def chunk_meetings_by_date_only(course_to_meetings, data_dir):
    """
    Chunks all meetings purely by date without any other grouping.
    
    Directory structure: /meetings/date/MM/DD/YY/meetings.json
    """
    # Flatten all meetings from all courses
    all_meetings = []
    for course_identifier, meetings in course_to_meetings.items():
        if meetings:
            all_meetings.extend(meetings)
    
    logger.info(f"Processing {len(all_meetings)} total meetings for pure date chunking")
    
    # Use the generic chunking function with just "meetings/date" as base directory
    directory_tuple = ("meetings", "date")
    files_written = chunk_meetings_by_date(all_meetings, directory_tuple, data_dir)
    
    logger.info(f"Wrote {files_written} meeting files organized purely by date")

def convert_keys_to_str(data):
    if isinstance(data, dict):
        return {str(key): convert_keys_to_str(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_keys_to_str(item) for item in data]
    else:
        return data


def recursive_sort_data(data):
    """
    Recursively sorts only dictionary keys.
    - For dicts, returns a new dict with keys in sorted order and values recursively processed.
    - For lists, tuples or sets, preserves the original order/structure but recurses into elements.
    - For JsonSerializable, converts to JSON and then sorts keys.
    """
    # If it's a dict, sort its keys
    if isinstance(data, dict):
        return {
            key: recursive_sort_data(data[key])
            for key in sorted(data.keys())
        }

    # If it's a list or tuple, preserve order but recurse
    if isinstance(data, list):
        return [recursive_sort_data(item) for item in data]
    if isinstance(data, tuple):
        return tuple(recursive_sort_data(item) for item in data)

    # Sets have no inherent order—just recurse and rebuild
    if isinstance(data, set):
        return sorted([recursive_sort_data(item) for item in data], key=str)

    # If it's JsonSerializable, convert to a dict and sort that
    if isinstance(data, JsonSerializable):
        return recursive_sort_data(data.to_dict())

    # Anything else (int, str, etc.) just return as-is
    return data


def format_file_size(size_in_bytes):
    """
    Formats the file size in human-readable units (Bytes, KB, MB, etc.).
    """
    units = ["Bytes", "KB", "MB", "GB", "TB"]
    index = 0
    size = size_in_bytes
    while size >= 1024 and index < len(units) - 1:
        size /= 1024
        index += 1
    return f"{size:.2f} {units[index]}"


def write_file(directory, directory_tuple: tuple[str, ...], filename: str, data):
    """
    Writes a sorted dictionary or list to a JSON file.
    - directory_tuple: Tuple representing the directory path.
    - filename: Name of the JSON file (without the .json extension).
    - data: Dictionary or list to be written to the file.
    """

    if not data:
        logger.warning(f"Data is empty for {filename}. Skipping writing to file.")
        return

    if not isinstance(data, (dict, list, set, tuple, JsonSerializable)):
        raise TypeError("Data must be a dictionary, list, set, tuple, or JsonSerializable object")

    # Convert keys to strings
    if isinstance(data, dict):
        data = convert_keys_to_str(data)

    # Convert data to a list if it is a set or tuple
    if isinstance(data, (set, tuple)):
        data = list(data)
    elif isinstance(data, JsonSerializable):
        data = data.to_dict()

    # Sort the data
    sorted_data = recursive_sort_data(data)

    # Sanitize directory components
    sanitized_directory = []
    for dir_component in directory_tuple:
        sanitized_component = sanitize_entry(dir_component)
        if sanitized_component is None:
            logger.warning(f"Directory component '{dir_component}' could not be sanitized. Skipping file write.")
            return
        sanitized_directory.append(sanitized_component)

    # Create the full directory path
    directory_path = os.path.join(directory, *sanitized_directory)

    # Ensure the directory exists
    os.makedirs(directory_path, exist_ok=True)

    # Sanitize the filename to remove problematic characters
    sanitized_filename = sanitize_entry(filename)

    if sanitized_filename is None:
        return

    # Full path to the JSON file
    file_path = os.path.join(directory_path, f"{sanitized_filename}.json")

    # Write the sorted data to the file in JSON format
    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(sorted_data, json_file, indent=4)

    # Calculate file size and format it
    file_size = os.path.getsize(file_path)
    readable_size = format_file_size(file_size)

    logger.debug(f"Data written to {file_path} ({readable_size})")


def wipe_data(data_dir):
    """
    Wipe only .json files in the data directory.
    """
    logger.info("Wiping .json files in the data directory...")

    # Remove only files ending with .json in the data directory
    for root, dirs, files in os.walk(data_dir, topdown=False):
        for file in files:
            if file.endswith(".json"):
                os.remove(os.path.join(root, file))

    logger.info("Wiping complete. Only .json files were removed.")


def write_data(
        data_dir,
        base_url,
        subject_to_full_subject,
        identifier_to_course,
        global_graph,
        subject_to_graph,
        course_to_graph,
        global_style,
        subject_to_style,
        instructor_to_rating: dict[str, FullInstructor],
        terms,
        quick_statistics,
        explorer_stats,
        course_to_meetings,
):
    wipe_data(data_dir)

    write_file(data_dir, tuple(), "subjects", subject_to_full_subject)

    for identifier, course in tqdm(identifier_to_course.items(), desc="Courses", unit="course"):
        write_file(data_dir, ("course",), identifier, course)

    write_file(data_dir, tuple(), "global_graph", global_graph)

    for subject, graph in tqdm(subject_to_graph.items(), desc="Graphs by Subject", unit="subject"):
        write_file(data_dir, ("graphs",), subject, graph)

    for course, graph in tqdm(course_to_graph.items(), desc="Graphs by Course", unit="course"):
        write_file(data_dir, ("graphs", "course"), course, graph)

    write_file(data_dir, tuple(), "global_style", global_style)

    for subject, style in tqdm(subject_to_style.items(), desc="Styles by Subject", unit="subject"):
        write_file(data_dir, ("styles",), subject, style)

    for instructor, rating in tqdm(instructor_to_rating.items(), desc="Instructors", unit="instructor"):
        if rating is None:
            continue
        write_file(data_dir, ("instructors",), instructor, rating)

    write_file(data_dir, tuple(), "terms", terms)

    write_file(data_dir, tuple(), "quick_statistics", quick_statistics)

    for key, value in tqdm(explorer_stats.items(), desc="Explorer Stats", unit="Stat"):
        write_file(data_dir, ("stats",), key, value)

    for course_identifier, meetings in tqdm(course_to_meetings.items(), desc="Course Meetings", unit="course"):
        if meetings:
            write_file(data_dir, ("course", course_identifier), "meetings", meetings)
    
    # Chunk meetings by date and building
    chunk_meetings_by_date_and_building(course_to_meetings, data_dir)
    
    # Chunk meetings by date and instructor
    chunk_meetings_by_date_and_instructor(course_to_meetings, data_dir)
    
    # Chunk meetings by date and subject
    chunk_meetings_by_date_and_subject(course_to_meetings, data_dir)
    
    # Chunk meetings purely by date
    chunk_meetings_by_date_only(course_to_meetings, data_dir)

    updated_on = datetime.now(timezone.utc).isoformat()
    updated_json = {
        "updated_on": updated_on,
    }

    write_file(data_dir, tuple(), "update", updated_json)

    subject_names = list(subject_to_graph.keys())
    course_names = list(identifier_to_course.keys())
    instructor_names = [key for key, value in instructor_to_rating.items() if value is not None]

    generate_sitemap(data_dir, base_url, subject_names, course_names, instructor_names)


def list_files(directory, directory_tuple: tuple[str, ...], extensions: tuple[str, ...]) -> list[str]:
    """
    Lists files in a specified directory that match the given file extensions.

    - directory: Base directory.
    - directory_tuple: Tuple representing the subdirectory path.
    - extensions: Tuple of file extensions to filter by (e.g., (".json", ".txt")).

    Returns:
    - List of filenames (as strings) that have one of the specified extensions.
    """
    # Create the full directory path
    directory_path = os.path.join(directory, *directory_tuple)

    if not os.path.isdir(directory_path):
        logger.error(f"Directory does not exist: {directory_path}")
        raise NotADirectoryError(f"{directory_path} is not a valid directory")

    # List files that match the given extensions
    file_list = []
    for file in os.listdir(directory_path):
        file_path = os.path.join(directory_path, file)
        if os.path.isfile(file_path) and file.endswith(extensions):
            file_list.append(file)

    # Sort the file list for consistency
    file_list.sort()

    logger.info(f"Found {len(file_list)} file(s) in {directory_path} with extensions: {extensions}")
    return file_list
