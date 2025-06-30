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
from building_highlight import generate_building_highlight_geojson

logger = getLogger(__name__)


def chunk_meetings_by_building(course_ref_to_meetings, data_dir):
    """
    Chunks meetings by building, writing them to organized directories.
    
    Args:
        course_ref_to_meetings: Dict mapping course references to lists of Meeting objects
        data_dir: Base data directory for writing files
    
    Directory structure: /buildings/{building_name}/meetings.json
    """
    # Group meetings by building
    building_meetings = defaultdict(list)
    
    # Flatten all meetings from all courses and group by building
    all_meetings = []
    for course_reference, meetings in course_ref_to_meetings.items():
        if meetings:
            all_meetings.extend(meetings)
    
    logger.info(f"Processing {len(all_meetings)} total meetings for building chunking")
    
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
    
    # Write meetings for each building to a single file
    total_files_written = 0
    for building_name, meetings in tqdm(building_meetings.items(), desc="Writing meeting files by building", unit="building"):
        directory_tuple = ("buildings", building_name)
        write_file(data_dir, directory_tuple, "meetings", meetings)
        total_files_written += 1
    
    logger.info(f"Wrote {total_files_written} meeting files organized by building")
    logger.info(f"Meetings organized across {len(building_meetings)} buildings")

def chunk_meetings_by_instructor(course_ref_to_meetings, data_dir):
    """
    Chunks meetings by instructor.
    
    Directory structure: /instructors/{instructor_name}/meetings.json
    """
    # Group meetings by instructor
    instructor_meetings = defaultdict(list)
    
    # Flatten all meetings from all courses and group by instructor
    all_meetings = []
    for course_reference, meetings in course_ref_to_meetings.items():
        if meetings:
            all_meetings.extend(meetings)
    
    logger.info(f"Processing {len(all_meetings)} total meetings for instructor chunking")
    
    for meeting in all_meetings:
        # Skip meetings without start_time or instructors
        if not meeting.start_time or not meeting.instructors:
            continue
            
        # Add meeting to each instructor's bucket (meetings can have multiple instructors)
        for instructor_name in meeting.instructors:
            instructor_meetings[instructor_name].append(meeting)
    
    # Write meetings for each instructor to a single file
    total_files_written = 0
    for instructor_name, meetings in tqdm(instructor_meetings.items(), desc="Writing meeting files by instructor", unit="instructor"):
        directory_tuple = ("instructors", instructor_name)
        write_file(data_dir, directory_tuple, "meetings", meetings)
        total_files_written += 1
    
    logger.info(f"Wrote {total_files_written} meeting files organized by instructor")
    logger.info(f"Meetings organized across {len(instructor_meetings)} instructors")

def chunk_meetings_by_subject(course_ref_to_meetings, data_dir):
    """
    Chunks meetings by subject using actual course reference subjects.
    
    Directory structure: /subjects/{subject_code}/meetings.json
    """
    # Group meetings by subject using actual course reference subjects
    subject_meetings = defaultdict(list)
    
    logger.info(f"Processing {len(course_ref_to_meetings)} courses for subject chunking")
    
    for course_reference, meetings in course_ref_to_meetings.items():
        if not meetings:
            continue
            
        # Use actual subjects from course reference (can have multiple subjects)
        for subject_code in course_reference.subjects:
            # Add all meetings for this course to each subject bucket
            subject_meetings[subject_code].extend(meetings)
    
    # Write meetings for each subject to a single file
    total_files_written = 0
    for subject_code, meetings in tqdm(subject_meetings.items(), desc="Writing meeting files by subject", unit="subject"):
        directory_tuple = ("subjects", subject_code)
        write_file(data_dir, directory_tuple, "meetings", meetings)
        total_files_written += 1
    
    logger.info(f"Wrote {total_files_written} meeting files organized by subject")
    logger.info(f"Meetings organized across {len(subject_meetings)} subjects")

def chunk_meetings_by_date_only(course_ref_to_meetings, data_dir):
    """
    Chunks all meetings purely by date without any other grouping.
    
    Directory structure: /meetings/MM-DD-YY.json
    """
    # Use US/Central timezone which automatically handles DST
    central_tz = ZoneInfo("US/Central")
    
    # Group meetings by date
    date_meetings = defaultdict(list)
    
    # Flatten all meetings from all courses
    all_meetings = []
    for course_reference, meetings in course_ref_to_meetings.items():
        if meetings:
            all_meetings.extend(meetings)
    
    logger.info(f"Processing {len(all_meetings)} total meetings for pure date chunking")
    
    for meeting in all_meetings:
        # Skip meetings without start_time
        if not meeting.start_time:
            continue
            
        # Convert epoch ms to datetime in Central Time
        start_datetime = datetime.fromtimestamp(meeting.start_time / 1000, tz=central_tz)
        
        # Extract date components and create filename
        year = start_datetime.strftime("%y")  # 2-digit year
        month = start_datetime.strftime("%m")  # 2-digit month
        day = start_datetime.strftime("%d")    # 2-digit day
        
        # Create filename with date
        date_filename = f"{month}-{day}-{year}"
        
        # Add meeting to the appropriate date bucket
        date_meetings[date_filename].append(meeting)
    
    # Write meetings for each date to flat files and generate GeoJSON building highlights
    files_written = 0
    geojson_files_written = 0
    osm_geojson_path = os.path.join(os.path.dirname(__file__), "osm.geojson")
    
    for date_filename, meetings_for_date in tqdm(date_meetings.items(), desc="Writing meeting files by date", unit="date"):
        directory_tuple = ("meetings",)
        
        # Write JSON file with meeting data
        write_file(data_dir, directory_tuple, date_filename, meetings_for_date)
        files_written += 1
        
        # Generate and write GeoJSON building highlight file
        try:
            building_geojson = generate_building_highlight_geojson(meetings_for_date, osm_geojson_path)
            if building_geojson and building_geojson.get('features'):
                write_geojson_file(data_dir, directory_tuple, date_filename, building_geojson)
                geojson_files_written += 1
            else:
                logger.warning(f"No building highlights generated for {date_filename}")
        except Exception as e:
            logger.error(f"Failed to generate building highlights for {date_filename}: {e}")
    
    logger.info(f"Wrote {files_written} meeting files organized purely by date")
    logger.info(f"Wrote {geojson_files_written} building highlight GeoJSON files")

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


def write_geojson_file(directory, directory_tuple: tuple[str, ...], filename: str, geojson_data):
    """
    Writes GeoJSON data to a .geojson file.
    - directory_tuple: Tuple representing the directory path.
    - filename: Name of the GeoJSON file (without the .geojson extension).
    - geojson_data: GeoJSON data to be written to the file.
    """
    if not geojson_data:
        logger.warning(f"GeoJSON data is empty for {filename}. Skipping writing to file.")
        return

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

    # Full path to the GeoJSON file
    file_path = os.path.join(directory_path, f"{sanitized_filename}.geojson")

    # Write the GeoJSON data to the file
    with open(file_path, 'w', encoding='utf-8') as geojson_file:
        json.dump(geojson_data, geojson_file, indent=2)

    # Calculate file size and format it
    file_size = os.path.getsize(file_path)
    readable_size = format_file_size(file_size)

    logger.debug(f"GeoJSON data written to {file_path} ({readable_size})")


def wipe_data(data_dir):
    """
    Wipe .json and .geojson files in the data directory.
    """
    logger.info("Wiping .json and .geojson files in the data directory...")

    # Remove files ending with .json or .geojson in the data directory
    for root, dirs, files in os.walk(data_dir, topdown=False):
        for file in files:
            if file.endswith((".json", ".geojson")):
                os.remove(os.path.join(root, file))

    logger.info("Wiping complete. .json and .geojson files were removed.")


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
        course_ref_to_meetings,
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

    for course_reference, meetings in tqdm(course_ref_to_meetings.items(), desc="Course Meetings", unit="course"):
        if meetings:
            course_identifier = course_reference.get_identifier()
            write_file(data_dir, ("course", course_identifier), "meetings", meetings)
    
    # Chunk meetings by building
    chunk_meetings_by_building(course_ref_to_meetings, data_dir)
    
    # Chunk meetings by instructor
    chunk_meetings_by_instructor(course_ref_to_meetings, data_dir)
    
    # Chunk meetings by subject
    chunk_meetings_by_subject(course_ref_to_meetings, data_dir)
    
    # Chunk meetings purely by date
    chunk_meetings_by_date_only(course_ref_to_meetings, data_dir)

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
