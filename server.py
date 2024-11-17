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

open_ai_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=open_ai_key)
stats = {
    "total_tokens": 0,
    "removed_requisites": 0,
}

app = Flask(__name__)
CORS(app)

sitemap_url = "https://guide.wisc.edu/sitemap.xml"

def get_embedding(text, model="text-embedding-3-small"):
    """
    Generates an embedding for the given text using OpenAI's embeddings API.
    """
    response = client.embeddings.create(input=text, model=model)
    stats["total_tokens"] += response.usage.total_tokens
    return response.data[0].embedding

def cosine_similarity(vec_a, vec_b):
    """
    Computes the cosine similarity between two vectors.
    """
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))

def remove_extra_spaces(text):
    return re.sub(r"\s+", " ", text).strip()

def parse_course_reference(course_code):
    """Remove special HTML characters and clean up the course code."""
    if not course_code:
        return None
    course_code = remove_extra_spaces(course_code)
    return (
        course_code
        .replace("\u200b", " ")
        .replace("\u00a0", " ")
        .strip()
    )

class CourseReference:
    def __init__(self, subjects, course_number):
        self.subjects = subjects
        self.course_number = course_number

    @classmethod
    def from_string(cls, course_reference_str):
        match = re.match(r"(\D+)(\d+)", course_reference_str)
        course_subject_str = match.group(1).replace(" ", "").strip()  # Only keep the subject
        course_subject = set(course_subject_str.split("/"))
        course_number = int(match.group(2).strip())  # Convert to integer
        return CourseReference(course_subject, course_number)

    def to_identifier(self):
        subjects = "/".join(self.subjects)
        return f"{subjects} {self.course_number}"

    def to_dict(self):
        return {
            "subjects": list(self.subjects),
            "course_number": self.course_number,
        }

    def __eq__(self, other):
        if not isinstance(other, CourseReference):
            return False
        return self.subjects == other.subjects and self.course_number == other.course_number

    def __hash__(self):
        return hash(self.to_identifier())

    def __repr__(self):
        return f"CourseReference(subjects={self.subjects}, course_number={self.course_number})"

class Course:
    def __init__(self, course_reference: CourseReference, course_title, description, prerequisites):
        self.course_reference = course_reference
        self.course_title = course_title
        self.description = description
        self.prerequisites = prerequisites

    def to_dict(self):
        return {
            "course_reference": self.course_reference.to_dict(),
            "course_title": self.course_title,
            "description": self.description,
            "prerequisites": self.prerequisites.to_dict()
        }

    @classmethod
    def from_block(cls, block):
        html_title = block.find("p", class_="courseblocktitle noindent")

        if not html_title:
            return None

        course_reference_str = html_title.find("span", class_="courseblockcode").get_text(strip=True)
        course_reference_str = parse_course_reference(course_reference_str)
        if not course_reference_str:
            return None
        course_reference = CourseReference.from_string(course_reference_str)

        raw_title = html_title.get_text(strip=True)
        raw_course_title = raw_title.replace(course_reference_str, "").strip()
        course_title = raw_course_title.split("—", 1)[-1].strip() if "—" in raw_course_title else raw_course_title

        description = block.find("p", class_="courseblockdesc noindent").get_text(strip=True)

        cb_extras = block.find("div", class_="cb-extras")
        if not cb_extras:
            return Course(course_reference, course_title, description, set())

        requisites_data = cb_extras.find("span", class_="cbextra-label", string=re.compile("Requisites:")).find_next("span", class_="cbextra-data")
        requisites_text = requisites_data.get_text(strip=True)
        requisites_links = requisites_data.find_all("a")
        requisites_courses = set()
        for link in requisites_links:
            title = link.get("title", "").strip()
            course_reference_str = parse_course_reference(title)
            requisites_courses.add(CourseReference.from_string(course_reference_str))

        requisites_courses.discard(course_reference)  # Remove self-reference

        course_prerequisite = CoursePrerequisites(requisites_text, requisites_courses)
        return Course(course_reference, course_title, description, course_prerequisite)

    def determine_parent(self):
        parent = None
        subjects = self.course_reference.subjects
        if len(subjects) > 1:
            parent = "CROSSLISTED"
        elif len(subjects) == 1:
            parent = next(iter(subjects))
        return parent

    def create_node(self):
        if self.determine_parent() != "CROSSLISTED":
            return frozendict({
                "data": frozendict({
                    "id": self.get_identifier(),
                    "parent": self.determine_parent(),
                    "description": self.description,
                }),
            })
        # Crosslisted courses are not children of a subject
        return frozendict({
            "data": frozendict({
                "id": self.get_identifier(),
                "description": self.description,
            }),
        })

    def create_edge(self, reference):
        return frozendict({
            "data": frozendict({
                "source": reference.to_identifier(),
                "target": self.get_identifier(),
            }),
        })

    def create_parent(self):
        return frozendict({
            "data": frozendict({
                "id": self.determine_parent(),
                "type": "compound",
            }),
        })

    def get_identifier(self):
        return self.course_reference.to_identifier()

    def get_subgraphs(self, courses, seen, graph_set_1, graph_set_2):
        if self.get_identifier() in seen:
            return
        seen.add(self.get_identifier())
        to_add = set()
        to_add.add(self.create_node())
        to_add.add(self.create_parent())
        for reference in self.prerequisites.course_references:
            if reference not in courses:
                print(f"Prerequisite not found in courses: {reference}")
                continue
            to_add.add(self.create_edge(reference))
            to_add.add(courses[reference].get_subgraphs(courses, seen, graph_set_1, graph_set_2))

        for graph_data in to_add:
            graph_set_1.add(graph_data)
            graph_set_2.add(graph_data)

    def get_short_summary(self):
        return f"""Course Title: {self.course_reference.to_identifier()} - {self.course_title}
        Course Description: {self.description}
        """

    def get_full_summary(self):
        req = self.prerequisites.prerequisites_text
        return f"""{self.get_short_summary()}
        Prerequisites: {req}
        """

    @classmethod
    def find_best_prerequisite(cls, course, prerequisites):
        """
        Finds the most relevant prerequisite for a given course using embeddings.

        Args:
            course: A Course object with attributes `description`.
            prerequisites: A list of Course objects, each with `description`.

        Returns:
            The most relevant prerequisite course.
        """
        # Get embedding for the main course
        course_embedding = get_embedding(course.get_full_summary())

        # Get embeddings for all prerequisites
        prerequisite_embeddings = [
            (prereq, get_embedding(prereq.get_short_summary())) for prereq in prerequisites
        ]

        # Compute similarity scores
        similarities = [
            (prereq, cosine_similarity(course_embedding, prereq_embedding))
            for prereq, prereq_embedding in prerequisite_embeddings
        ]

        # Find the prerequisite with the highest similarity score
        best_prerequisite = max(similarities, key=lambda x: x[1])

        # Return the course object of the best prerequisite
        return best_prerequisite[0]

    def optimize_prerequisites(self, course_ref_course, stats):
        if len(self.prerequisites.course_references) <= 1:
            return

        c = set()
        for reference in self.prerequisites.course_references:
            if reference not in course_ref_course:
                print(f"Prerequisite not found in courses: {reference}")
                continue
            course = course_ref_course[reference]
            c.add(course)


        best = self.find_best_prerequisite(self, c)
        print(f"Selected {best} as the best prerequisite for {self.get_identifier()} out of {len(c)} options")
        stats["removed_requisites"] += len(self.prerequisites.course_references) - 1
        self.prerequisites.course_references = {best.course_reference}

    def __eq__(self, other):
        return self.get_identifier() == other.get_identifier() and self.course_title == other.course_title and self.description == other.description

    def __hash__(self):
        return hash(self.get_identifier())

    def __repr__(self):
        return self.get_identifier()


class CoursePrerequisites:
    def __init__(self, prerequisites_text, course_references):
        self.prerequisites_text = prerequisites_text
        self.course_references = course_references

    def to_dict(self):
        return {
            "prerequisites_text": self.prerequisites_text,
            "course_references": [course_ref.to_dict() for course_ref in self.course_references],
        }

    def __repr__(self):
        return f"CoursePrerequisite(prerequisites_text={self.prerequisites_text}, course_references={self.course_references})"

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
