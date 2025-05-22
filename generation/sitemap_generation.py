import os
from typing import Union
from xml.dom.minidom import parseString

from pathvalidate import validate_filename, ValidationError
from sitemap import Urlset, Siteindex, Url, Sitemap
from tqdm import tqdm

pages = [
    '',
    'explorer',
    'upload'
]

def sanitize_entry(entry, logger):

    result = entry.replace("/", "_").replace(" ", "_")

    try:
        validate_filename(result)
    except ValidationError as e:
        logger.debug(f"Invalid filename '{result}': {e}. Not writing file.")
        return None

    return result


def create_normal_url(base_url, url_str, logger, priority=0.5):
    sanitized_url = sanitize_entry(url_str, logger)
    if sanitized_url is None:
        return None
    url = Url(f'{base_url}/{sanitized_url}', changefreq='weekly', priority=priority)
    return url

def write_sitemap(data_dir, key, url_set: Urlset):
    raw = url_set.to_string()
    pretty = parseString(raw).toprettyxml()

    path = os.path.join(data_dir, f"{key}-sitemap.xml")

    with open(path, "w", encoding="utf-8") as f:
        f.write(pretty)

def write_siteindex(data_dir, siteindex: Siteindex):
    raw = siteindex.to_string()
    pretty = parseString(raw).toprettyxml()

    path = os.path.join(data_dir, "sitemap.xml")

    with open(path, "w", encoding="utf-8") as f:
        f.write(pretty)

def write_urlsets(data_dir, base_url, url_sets: dict[str, Urlset]):

    siteindex = Siteindex()

    for key, urlset in url_sets.items():
        write_sitemap(data_dir, key, urlset)
        sitemap = Sitemap(f'{base_url}/{key}-sitemap.xml')
        siteindex.add_sitemap(sitemap)

    write_siteindex(data_dir, siteindex)

def safe_url_set_add(url_set: Urlset, url: Url):
    if url is not None:
        url_set.add_url(url)

def generate_sitemap(data_dir, base_url, subjects, courses, instructors, logger):

    pages_urlset = Urlset()
    for page in pages:
        url = Url(f"{base_url}/{page}", changefreq='monthly', priority=1)
        safe_url_set_add(pages_urlset, url)

    subjects_urlset = Urlset()
    for subject in tqdm(subjects, desc="Explorer Sitemap", unit="subject"):
        url = create_normal_url(base_url, f"explorer/{subject}", logger, priority=0.9)
        safe_url_set_add(subjects_urlset, url)

    courses_urlset = Urlset()
    for course in tqdm(courses, desc="Course Sitemap", unit="course"):
        url = create_normal_url(base_url, f"courses/{course}", logger, priority=1.0)
        safe_url_set_add(courses_urlset, url)

    instructors_urlset = Urlset()
    for instructor in tqdm(instructors, desc="Instructor Sitemap", unit="instructor"):
        url = create_normal_url(base_url, f"instructors/{instructor}", logger, priority=0.8)
        safe_url_set_add(instructors_urlset, url)

    url_sets = {
        'pages': pages_urlset,
        'subjects': subjects_urlset,
        'courses': courses_urlset,
        'instructors': instructors_urlset
    }

    write_urlsets(data_dir, base_url, url_sets)





