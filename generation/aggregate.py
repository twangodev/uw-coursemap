from course import Course
from enrollment_data import GradeData
from instructors import FullInstructor


def aggregate_instructors(course_ref_to_course: dict[Course.Reference, Course], instructor_to_rating: dict[str, FullInstructor], logger):

    for course in course_ref_to_course.values():
        for term_data in course.term_data.values():

            if not term_data.grade_data or not term_data.grade_data.instructors:
                continue

            for instructor_name in term_data.grade_data.instructors:

                if instructor_name not in instructor_to_rating:
                    continue

                instructor = instructor_to_rating[instructor_name]

                if not instructor.courses_taught:
                    instructor.courses_taught = set()

                if not instructor.cumulative_grade_data:
                    instructor.cumulative_grade_data = GradeData(
                        total=0,
                        a=0,
                        ab=0,
                        b=0,
                        bc=0,
                        c=0,
                        d=0,
                        f=0,
                        satisfactory=0,
                        unsatisfactory=0,
                        credit=0,
                        no_credit=0,
                        passed=0,
                        incomplete=0,
                        no_work=0,
                        not_reported=0,
                        other=0,
                        instructors=set()
                    )

                course_reference = course.course_reference
                grade_data_summation = instructor.cumulative_grade_data.merge_with(term_data.grade_data)

                instructor.courses_taught.add(course_reference.get_identifier())
                instructor.cumulative_grade_data = grade_data_summation

