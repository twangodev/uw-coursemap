import json
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from collections import defaultdict
from logging import getLogger

from tqdm import tqdm

from instructors import FullInstructor
from json_serializable import JsonSerializable
from map import get_buildings
from sitemap_generation import generate_sitemap, sanitize_entry
from trips import TripGenerator

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


def chunk_meetings_by_building_and_date(course_ref_to_meetings, data_dir):
    """
    Chunks meetings by building and then by date, creating daily files for each building.
    
    Args:
        course_ref_to_meetings: Dict mapping course references to lists of Meeting objects
        data_dir: Base data directory for writing files
    
    Directory structure: 
        /buildings/{building_name}/MM-DD-YY.json - Meeting data for each day
        /buildings/{building_name}/MM-DD-YY.geojson - Building highlights for each day
        /buildings/{building_name}/index.json - Index of all dates with statistics
    """
    # Group meetings by building
    building_meetings = defaultdict(list)
    
    # Flatten all meetings from all courses and group by building
    all_meetings = []
    for course_reference, meetings in course_ref_to_meetings.items():
        if meetings:
            all_meetings.extend(meetings)
    
    logger.info(f"Processing {len(all_meetings)} total meetings for building and date chunking")
    
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
    
    # Process each building's meetings by date
    total_buildings_processed = 0
    total_date_files_written = 0
    
    for building_name, meetings in tqdm(building_meetings.items(), desc="Writing daily meeting files by building", unit="building"):
        directory_tuple = ("buildings", building_name)
        
        # Use the abstracted function to write meetings by date for this building
        write_meetings_by_date(meetings, data_dir, directory_tuple)
        
        total_buildings_processed += 1
        # Note: write_meetings_by_date handles the counting of individual date files
    
    logger.info(f"Processed {total_buildings_processed} buildings with daily meeting files")
    logger.info(f"Each building now has MM-DD-YY.json, MM-DD-YY.geojson, and index.json files")

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
    Also creates an index.json file with date mappings and statistics.
    """
    # Flatten all meetings from all courses
    all_meetings = []
    for course_reference, meetings in course_ref_to_meetings.items():
        if meetings:
            all_meetings.extend(meetings)
    
    logger.info(f"Processing {len(all_meetings)} total meetings for pure date chunking")
    
    # Use the abstracted function to write meetings by date
    write_meetings_by_date(all_meetings, data_dir, ("meetings",))


def write_meetings_by_date(meetings, data_dir, directory_tuple):
    """
    Abstract function to write meetings grouped by date to any directory structure.
    
    Args:
        meetings: List of meeting objects to process
        data_dir: Base data directory
        directory_tuple: Tuple representing the directory path (e.g., ("meetings",) or ("buildings", "building_name"))
    
    Creates:
        - MM-DD-YY.json files with meeting data
        - MM-DD-YY.geojson files with building highlights
        - index.json file with date mappings and statistics
    """
    # Use US/Central timezone which automatically handles DST
    central_tz = ZoneInfo("US/Central")
    
    # Group meetings by date
    date_meetings = defaultdict(list)
    # Track unique buildings per date for index.json
    date_buildings = defaultdict(set)
    # Track unique instructors per date for index.json
    date_instructors = defaultdict(set)
    # Track total students per date for index.json
    date_students = defaultdict(int)
    
    for meeting in meetings:
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
        
        # Track unique buildings for this date
        if meeting.location and meeting.location.building:
            date_buildings[date_filename].add(meeting.location.building)
        
        # Track unique instructors for this date
        if meeting.instructors:
            for instructor in meeting.instructors:
                date_instructors[date_filename].add(instructor)
        
        # Track total students for this date
        if meeting.current_enrollment:
            date_students[date_filename] += meeting.current_enrollment
    
    # Write meetings for each date to flat files and generate GeoJSON building highlights
    files_written = 0
    geojson_files_written = 0

    for date_filename, meetings_for_date in tqdm(date_meetings.items(), desc="Writing meeting files by date", unit="date"):
        # Write JSON file with meeting data
        write_file(data_dir, directory_tuple, date_filename, meetings_for_date)
        files_written += 1

        # Generate building highlights for this date
        building_geojson, metadata = get_buildings(meetings_for_date)

        full_geojson = {
            "type": "FeatureCollection",
            "features": building_geojson.features,
            "metadata": {
                "total_buildings": len(building_geojson.features),
                "total_meetings": len(meetings_for_date),
                "max_persons": metadata.get('max_persons', 0),
                "total_chunks": metadata.get('total_chunks', 0),
                "chunk_duration_minutes": metadata.get('chunk_duration_minutes', 5),
                "start_time": metadata.get('start_time'),
                "end_time": metadata.get('end_time'),
                "total_persons": metadata.get('total_persons', []),
                "total_instructors": metadata.get('total_instructors', [])
            }
        }

        if building_geojson:
            write_geojson_file(data_dir, directory_tuple, date_filename, full_geojson)
            geojson_files_written += 1
        else:
            logger.warning(f"No building highlights generated for {date_filename}")

    # Create index.json with date mappings and statistics
    index_data = {}
    for date_filename in date_meetings.keys():
        index_data[date_filename] = {
            "total_buildings": len(date_buildings[date_filename]),
            "total_meetings": len(date_meetings[date_filename]),
            "total_instructors": len(date_instructors[date_filename]),
            "total_students": date_students[date_filename]
        }
    
    # Write index.json file
    write_file(data_dir, directory_tuple, "index", index_data)
    
    logger.info(f"Wrote {files_written} meeting files organized by date to {'/'.join(directory_tuple)}")
    logger.info(f"Wrote {geojson_files_written} building highlight GeoJSON files to {'/'.join(directory_tuple)}")
    logger.info(f"Created index.json with {len(index_data)} date entries in {'/'.join(directory_tuple)}")

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


def generate_trips_data(data_dir):
    """
    Generate trips data for traffic visualization.
    """
    try:
        logger.info("Generating trips data for visualization...")
        
        # Initialize the trip generator
        traffic_file = os.path.join(os.path.dirname(__file__), 'traffic.geojson')
        if not os.path.exists(traffic_file):
            logger.warning(f"Traffic file not found at {traffic_file}. Skipping trip generation.")
            return
        
        generator = TripGenerator(traffic_file)
        
        # Define parameters for Madison, WI area
        center_point = (-89.40902500577803, 43.073265957414826)
        radius_meters = 8000
        inner_radius_meters = 5 * 1609.34  # 5 miles converted to meters
        num_trips = 1000
        
        # Generate trips
        trips = generator.generate_trips(
            center=center_point,
            radius_meters=radius_meters,
            num_trips=num_trips,
            time_period_hours=1,
            inner_radius_meters=inner_radius_meters
        )
        
        # Export trips data directly using TripGenerator's export method
        output_path = os.path.join(data_dir, 'trips.json')
        TripGenerator.export_trips_json(trips, output_path)
        
        logger.info(f"Successfully generated {len(trips)} trips and saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to generate trips data: {e}")
        # Don't let trip generation failure stop the rest of the data processing


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
    
    # Chunk meetings by building and date (creates daily files for each building)
    chunk_meetings_by_building_and_date(course_ref_to_meetings, data_dir)
    
    # Chunk meetings by instructor
    chunk_meetings_by_instructor(course_ref_to_meetings, data_dir)
    
    # Chunk meetings by subject
    chunk_meetings_by_subject(course_ref_to_meetings, data_dir)
    
    # Chunk meetings purely by date
    chunk_meetings_by_date_only(course_ref_to_meetings, data_dir)
    
    # Generate trips data for visualization
    generate_trips_data(data_dir)

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
