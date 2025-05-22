import os
from typing import List, Dict, Union
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString
from pathvalidate import validate_filename, ValidationError
from tqdm import tqdm

pages = ['', 'explorer', 'upload']

def sanitize_entry(entry: str, logger) -> Union[str, None]:
    result = entry.replace("/", "_").replace(" ", "_")
    try:
        validate_filename(result)
    except ValidationError as e:
        logger.debug(f"Invalid filename '{result}': {e}. Not writing file.")
        return None
    return result

def create_url_entry(base_url: str, prefix: str, url_str: str, logger,
                     changefreq: str = 'weekly',
                     priority: float = 0.5) -> Union[Dict[str, Union[str, float]], None]:
    sanitized = sanitize_entry(url_str, logger)
    if not sanitized:
        return None
    return {
        'loc': f"{base_url}/{prefix}/{sanitized}",
        'changefreq': changefreq,
        'priority': priority
    }

def generate_sitemap_xml(urls: List[Dict[str, Union[str, float]]]) -> str:
    urlset = Element('urlset', xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for entry in urls:
        url_el = SubElement(urlset, 'url')
        loc = SubElement(url_el, 'loc')
        loc.text = entry['loc']
        cf = SubElement(url_el, 'changefreq')
        cf.text = entry['changefreq']
        pr = SubElement(url_el, 'priority')
        pr.text = f"{entry['priority']:.1f}"
    raw_xml = tostring(urlset, encoding='utf-8')
    return parseString(raw_xml).toprettyxml(indent="  ")

def generate_siteindex_xml(sitemap_urls: List[str]) -> str:
    idx = Element('sitemapindex', xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for loc_url in sitemap_urls:
        sm = SubElement(idx, 'sitemap')
        loc = SubElement(sm, 'loc'); loc.text = loc_url
    raw_xml = tostring(idx, encoding='utf-8')
    return parseString(raw_xml).toprettyxml(indent="  ")

def write_sitemap(data_dir: str, key: str, url_entries: List[Dict]):
    xml = generate_sitemap_xml(url_entries)
    path = os.path.join(data_dir, f"{key}-sitemap.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml)

def write_siteindex(data_dir: str, sitemap_urls: List[str]):
    xml = generate_siteindex_xml(sitemap_urls)
    path = os.path.join(data_dir, "sitemap.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml)

def write_urlsets(data_dir: str, base_url: str,
                  url_sets: Dict[str, List[Dict[str,Union[str,float]]]]):
    sitemap_urls: List[str] = []
    for key, entries in url_sets.items():
        write_sitemap(data_dir, key, entries)
        sitemap_urls.append(f"{base_url}/{key}-sitemap.xml")
    write_siteindex(data_dir, sitemap_urls)

def generate_sitemap(data_dir: str, base_url: str,
                     subjects: List[str], courses: List[str],
                     instructors: List[str], logger):
    pages_entries = [{'loc': f"{base_url}/{p}", 'changefreq': 'monthly', 'priority': 1.0}
                     for p in pages]

    subj_entries = []
    for subj in tqdm(subjects, desc="Explorer Sitemap", unit="subject"):
        entry = create_url_entry(base_url, "explorer", subj, logger, priority=0.9)
        if entry: subj_entries.append(entry)

    course_entries = []
    for crs in tqdm(courses, desc="Course Sitemap", unit="course"):
        entry = create_url_entry(base_url, "courses", crs, logger, priority=1.0)
        if entry: course_entries.append(entry)

    instr_entries = []
    for inst in tqdm(instructors, desc="Instructor Sitemap", unit="instructor"):
        entry = create_url_entry(base_url, "instructors", inst, logger, priority=0.8)
        if entry: instr_entries.append(entry)

    url_sets = {
        'pages': pages_entries,
        'subjects': subj_entries,
        'courses': course_entries,
        'instructors': instr_entries
    }

    write_urlsets(data_dir, base_url, url_sets)
