import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from frozendict import frozendict
from openai import OpenAI

from color import generate_random_hex_colors

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

sitemap_url = "https://guide.wisc.edu/sitemap.xml"




def get_course_blocks(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    return soup.find_all("div", class_="courseblock")

def add_data(course_ref_course, subject_course, blocks):
    for block in blocks:
        course = Course.from_block(block)
        if not course:
            continue
        course_ref_course[course.course_reference] = course

        for subject in course.course_reference.subjects:
            if subject not in subject_course:
                subject_course[subject] = set()
            subject_course[subject].add(course)

def get_sitemap_urls():
    print("Fetching and parsing the sitemap...")

    response = requests.get(sitemap_url)
    soup = BeautifulSoup(response.content, "xml")

    # Step 2: Extract guide-related URLs (only those containing '/guide/')
    site_map_urls = [url.text for url in soup.find_all("loc") if "/courses/" in url.text]

    print(f"Total guide links found: {len(site_map_urls)}")

    return site_map_urls

def build_data(site_map_urls):
    print("Building course data...")

    course_ref_course = dict()
    subject_course = dict()

    for url in site_map_urls:
        course_blocks = get_course_blocks(url)
        add_data(course_ref_course, subject_course, course_blocks)

    print(f"Total courses found: {len(course_ref_course)}")
    print(f"Total subjects found: {len(subject_course)}")
    return course_ref_course, subject_course

def build_graphs():
    print("Building course graphs...")

    graph = set()
    subject_graph = dict()

    for subject in subjects_course_map.keys():
        for course in subjects_course_map[subject]:
            if subject not in subject_graph:
                subject_graph[subject] = set()
            course.get_subgraphs(courses, set(), graph, subject_graph[subject])

    return graph, subject_graph

@app.route('/subjects', methods=['GET'])
def get_subjects():
    return jsonify(list(subjects_course_map.keys()))

@app.route('/graph/<subject>', methods=['GET'])
def get_subject_graph(subject):
    return jsonify(list(subject_graph_map[subject]))

@app.route('/graph/style/<subject>', methods=['GET'])
def get_subject_graph_style(subject):
    return styles[subject]

@app.route('/graphs', methods=['GET'])
def get_graphs():
    return jsonify(list(graphs))

@app.route('/graph/style', methods=['GET'])
def get_graph_styles():
    return global_style


def optimize_course(course, courses, stats, max_retries=3, timeout=30):
    """
    Optimize prerequisites for a single course with retries and timeout handling.

    Args:
        course: The course to optimize.
        courses: All courses (used for dependency lookup).
        client: OpenAI API client instance.
        token_usage: A dictionary to track token usage.
        max_retries: Maximum number of retries for a failed request.
        timeout: Timeout in seconds for each request.

    Returns:
        None (updates prerequisites in place).
    """
    retries = 0
    while retries < max_retries:
        try:
            # Optimize prerequisites (ensure the request doesn't exceed timeout)
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(course.optimize_prerequisites, courses, stats)
                return future.result(timeout=timeout)
        except Exception as e:
            retries += 1
            print(f"Retry {retries} for course {course.get_identifier()} failed: {e}")
            if retries >= max_retries:
                print(f"Optimization for course {course.get_identifier()} failed completely.")
                return None  # Abandon optimization if all retries fail

def optimize_prerequisites(courses, client, stats):
    """
    Optimizes prerequisites for all courses using multithreading.

    Args:
        courses: Dictionary of all courses.
        client: OpenAI API client instance.
        stats: A dictionary to track token usage.

    Returns:
        None (prints optimization status and token usage).
    """
    print("Optimizing prerequisites...")

    # Use ThreadPoolExecutor to handle multiple courses concurrently
    total_courses = len(courses)
    completed_courses = 0

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_course = {
            executor.submit(optimize_course, course, courses, stats): course
            for course in courses.values()
        }
        for future in as_completed(future_to_course):
            course = future_to_course[future]
            try:
                future.result()  # This will re-raise any exception from the thread
                completed_courses += 1
                remaining_courses = total_courses - completed_courses
                print(f"Optimization completed for course {course.get_identifier()}. {remaining_courses} courses remaining.")
            except Exception as e:
                completed_courses += 1
                remaining_courses = total_courses - completed_courses
                print(f"Optimization failed for course {course.get_identifier()}: {e}. {remaining_courses} courses remaining.")

    print(f"Prerequisites optimized. Total tokens used: {stats['total_tokens']}. Removed requisites: {stats['removed_requisites']}")

def cleanup_graphs():
    count = 0
    if None in graphs:
        count += 1
    graphs.discard(None)
    for subject in subject_graph_map:
        if None in subject_graph_map[subject]:
            count += 1
        subject_graph_map[subject].discard(None)
    print(f"Removed {count} None graphs")

def generate_style(parent, color):
    return { parent : color}

def generate_style_from_graph(graph):
    parents = set()
    for el in graph:
        if "data" in el:
            data = el["data"]
            if "parent" in data:
                parents.add(data["parent"])

    colors = generate_random_hex_colors(len(set(parents)))

    return [generate_style(parent, color) for parent, color in zip(set(parents), colors)]

def generate_styles():
    return { subject: generate_style_from_graph(subject_graph_map[subject]) for subject in subject_graph_map }

if __name__ == "__main__":
    urls = get_sitemap_urls()
    courses, subjects_course_map = build_data(urls)

    identifier_map = {course.get_identifier(): course for course in courses.values()}

    optimize_prerequisites(courses, client, stats)

    graphs, subject_graph_map = build_graphs()

    cleanup_graphs()

    styles = generate_styles()
    global_style = generate_style_from_graph(graphs)

    app.run(debug=False)
