from logging import Logger

from frozendict import frozendict

from color import generate_random_hex_colors
from course import Course


def create_compound(subject):
    return frozendict({
        "data": frozendict({
            "id": subject,
            "type": "compound",
        }),
    })


def create_node(course: Course):
    data = {
        "id": course.get_identifier(),
        "title": course.course_title,
        "description": course.description,
    }

    parent = course.determine_parent()
    if parent != "CROSSLISTED":
        data["parent"] = parent

    node = {"data": frozendict(data), }
    return frozendict(node)


def create_edge(target, source):
    return frozendict({
        "data": frozendict({
            "source": source,
            "target": target,
        }),
    })


def generate_style(parent, color):
    return {parent: color}


def get_subgraphs(course: Course, course_ref_to_course: dict[Course.Reference, Course], seen: set[Course],
                  graph_set_1: set[Course], graph_set_2: set[Course]):
    if course.get_identifier() in seen:
        return
    seen.add(course.get_identifier())
    to_add = set()

    to_add.add(create_node(course))
    to_add.add(create_compound(course.determine_parent()))

    for reference in course.optimized_prerequisites.course_references:
        if reference not in course_ref_to_course:
            print(f"Prerequisite not found in courses: {reference}")
            continue
        edge = create_edge(target=course.get_identifier(), source=reference.get_identifier())
        to_add.add(edge)
        c: Course = course_ref_to_course[reference]
        to_add.add(get_subgraphs(c, course_ref_to_course, seen, graph_set_1, graph_set_2))

    for graph_data in to_add:
        graph_set_1.add(graph_data)
        graph_set_2.add(graph_data)


def build_graphs(course_ref_to_course: dict[Course.Reference, Course], subject_to_courses: dict[str, set[Course]], logger: Logger):
    logger.info("Building course graphs...")

    graph = set()
    subject_to_graph = dict()

    for subject, course_set in subject_to_courses.items():
        for course in course_set:
            if subject not in subject_to_graph:
                subject_to_graph[subject] = set()
            get_subgraphs(course, course_ref_to_course, set(), graph, subject_to_graph[subject])

    return graph, subject_to_graph


def cleanup_graphs(global_graph, subject_to_graph, logger: Logger):
    count = 0
    if None in global_graph:
        count += 1
    global_graph.discard(None)
    for subject in subject_to_graph:
        if None in subject_to_graph[subject]:
            count += 1
        subject_to_graph[subject].discard(None)
    logger.info(f"Removed {count} None graphs")


def generate_style_from_graph(graph, color_map):
    parents = set()
    for el in graph:
        if "data" in el:
            data = el["data"]
            if "parent" in data:
                parents.add(data["parent"])

    colors = generate_random_hex_colors(parents, color_map)

    return [generate_style(parent, color) for parent, color in zip(set(parents), colors)]


def generate_styles(subject_to_graph, color_map):
    return {subject: generate_style_from_graph(subject_to_graph[subject], color_map) for subject in subject_to_graph}
