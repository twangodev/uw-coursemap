import type { Course as CourseSchema, WithContext, CourseInstance, AggregateRating, Person, Organization, EducationalOccupationalProgram, Offer, Place } from "schema-dts";
import type { Course } from "$lib/types/course.ts";
import type { FullInstructorInformation } from "$lib/types/instructor.ts";
import type { Terms } from "$lib/types/terms.ts";
import { courseReferenceToString } from "$lib/types/course.ts";
import { calculateGradePointAverage, calculateCompletionRate } from "$lib/types/madgrades.ts";
import { university } from "$lib/json-schemas.ts";

export function generateComprehensiveCourseJsonLd(
  course: Course,
  instructors: FullInstructorInformation[],
  terms: Terms,
  selectedTermId: string
): WithContext<CourseSchema> {
  const courseCode = courseReferenceToString(course.course_reference);
  const courseUrl = `https://uwcourses.com/courses/${courseCode.replace(/[\s\/]/g, '_')}`;
  
  // Get term-specific data
  const termData = course.term_data[selectedTermId];
  const enrollmentData = termData?.enrollment_data;
  const gradeData = termData?.grade_data || course.cumulative_grade_data;
  
  // Calculate ratings from grade data
  const aggregateRating = gradeData ? generateAggregateRating(gradeData, instructors) : undefined;
  
  // Get prerequisites as structured data
  const prerequisites = generatePrerequisitesList(course);
  
  // Get skills taught
  const skillsTaught = generateSkillsTaught(course);
  
  // Get course level
  const educationalLevel = getCourseLevel(course.course_reference.course_number);
  
  // Generate course instances
  const courseInstances = generateCourseInstances(course, instructors, terms, selectedTermId);
  
  // Build the comprehensive schema
  const schema: WithContext<CourseSchema> = {
    "@context": "https://schema.org",
    "@type": "Course",
    "@id": courseUrl,
    "url": courseUrl,
    "courseCode": courseCode,
    "name": course.course_title,
    "description": course.description,
    "provider": university,
    "inLanguage": "en-US",
    "educationalLevel": educationalLevel,
  };
  
  // Add credit information if available
  if (enrollmentData?.credit_count) {
    const [minCredits, maxCredits] = enrollmentData.credit_count;
    // Use average credits as a simple value since StructuredValue doesn't support ranges well
    schema.numberOfCredits = maxCredits;
  }
  
  // Add prerequisites
  if (prerequisites.length > 0) {
    schema.coursePrerequisites = prerequisites;
  }
  
  // Add skills/topics taught
  if (skillsTaught.length > 0) {
    schema.teaches = skillsTaught;
    schema.about = skillsTaught.slice(0, 5); // Top 5 topics
  }
  
  // Add ratings
  if (aggregateRating) {
    schema.aggregateRating = aggregateRating;
  }
  
  // Add course instances
  if (courseInstances.length > 0) {
    schema.hasCourseInstance = courseInstances;
  }
  
  // Add offers
  schema.offers = generateOffers(enrollmentData);
  
  // Add educational program context
  if (enrollmentData?.school) {
    schema.isPartOf = {
      "@type": "CreativeWork",
      "name": `${enrollmentData.school.name} Programs`,
      "url": enrollmentData.school.url
    };
  }
  
  // Add attributes
  if (enrollmentData?.general_education || enrollmentData?.ethnic_studies) {
    const attributes: string[] = [];
    if (enrollmentData.general_education) attributes.push("General Education");
    if (enrollmentData.ethnic_studies) attributes.push("Ethnic Studies");
    schema.educationalCredentialAwarded = attributes.join(", ") + " Credit";
  }
  
  // Add keywords
  schema.keywords = generateCourseKeywords(course);
  
  // Similar courses will be shown in the UI but not in schema
  // as isRelatedTo is not a valid property for Course type
  
  // Add total historical enrollment if available
  if (course.cumulative_grade_data?.total) {
    schema.totalHistoricalEnrollment = course.cumulative_grade_data.total;
  }
  
  return schema;
}

function generateAggregateRating(gradeData: any, instructors: FullInstructorInformation[]): AggregateRating | undefined {
  const gpa = calculateGradePointAverage(gradeData);
  if (!gpa) return undefined;
  
  // Convert GPA to 5-star rating (4.0 = 5 stars, 2.0 = 2.5 stars)
  const rating = (gpa / 4.0) * 5;
  
  // Get average instructor rating if available
  const instructorRatings = instructors
    .filter(i => i.rmp_data?.average_rating)
    .map(i => i.rmp_data!.average_rating);
  
  const avgInstructorRating = instructorRatings.length > 0
    ? instructorRatings.reduce((a, b) => a + b, 0) / instructorRatings.length
    : null;
  
  // Use instructor rating if available, otherwise use GPA-based rating
  const finalRating = avgInstructorRating || rating;
  
  return {
    "@type": "AggregateRating",
    "ratingValue": Number(finalRating.toFixed(1)),
    "bestRating": 5,
    "worstRating": 1,
    "ratingCount": gradeData.total || instructors.reduce((sum, i) => sum + (i.rmp_data?.num_ratings || 0), 0),
    "reviewCount": instructors.reduce((sum, i) => sum + (i.rmp_data?.num_ratings || 0), 0)
  };
}

function generatePrerequisitesList(course: Course): Array<string | CourseSchema> {
  const prerequisites: Array<string | CourseSchema> = [];
  
  // Add text prerequisites
  if (course.prerequisites?.prerequisites_text && course.prerequisites.prerequisites_text !== "None") {
    prerequisites.push(course.prerequisites.prerequisites_text);
  }
  
  // Add structured prerequisites
  const prereqCourses = course.optimized_prerequisites?.course_references || course.prerequisites?.course_references || [];
  prereqCourses.slice(0, 5).forEach(ref => {
    prerequisites.push({
      "@type": "Course",
      "courseCode": courseReferenceToString(ref),
      "url": `https://uwcourses.com/courses/${courseReferenceToString(ref).replace(/[\s\/]/g, '_')}`,
      "provider": university
    });
  });
  
  return prerequisites;
}

function generateSkillsTaught(course: Course): string[] {
  const skills: string[] = [];
  const title = course.course_title.toLowerCase();
  const description = course.description.toLowerCase();
  
  // Extract skills from title and description
  const skillPatterns = [
    /programming/i, /design/i, /analysis/i, /research/i, /writing/i,
    /problem solving/i, /critical thinking/i, /communication/i,
    /laboratory/i, /mathematical/i, /statistical/i, /computational/i
  ];
  
  skillPatterns.forEach(pattern => {
    if (pattern.test(title) || pattern.test(description)) {
      skills.push(pattern.source.replace(/\\/g, '').replace(/i$/, ''));
    }
  });
  
  // Add subject-specific skills
  const subject = course.course_reference.subjects[0];
  const subjectSkills: { [key: string]: string[] } = {
    "COMP SCI": ["Software Development", "Algorithm Design", "Data Structures"],
    "MATH": ["Mathematical Reasoning", "Proof Writing", "Quantitative Analysis"],
    "CHEM": ["Laboratory Techniques", "Chemical Analysis", "Scientific Method"],
    "PHYSICS": ["Problem Solving", "Mathematical Modeling", "Experimental Design"],
    "ENGLISH": ["Critical Reading", "Academic Writing", "Literary Analysis"]
  };
  
  if (subjectSkills[subject]) {
    skills.push(...subjectSkills[subject]);
  }
  
  return [...new Set(skills)];
}

function getCourseLevel(courseNumber: number): string {
  if (courseNumber < 300) return "Beginner";
  if (courseNumber < 500) return "Intermediate";
  if (courseNumber < 700) return "Advanced";
  return "Graduate";
}

function generateCourseInstances(
  course: Course,
  instructors: FullInstructorInformation[],
  terms: Terms,
  selectedTermId: string
): CourseInstance[] {
  const instances: CourseInstance[] = [];
  const termData = course.term_data[selectedTermId];
  
  if (!termData) return instances;
  
  // Get term information
  const termArray = (terms as any).terms || [];
  const termInfo = termArray.find((t: any) => t.code === selectedTermId);
  if (!termInfo) return instances;
  
  // Create instance for the selected term
  const instance: CourseInstance = {
    "@type": "CourseInstance",
    "courseMode": "on-campus",
    "name": `${course.course_title} - ${termInfo.name}`,
  };
  
  // Add schedule information if available
  if (termData.enrollment_data?.typically_offered) {
    instance.courseSchedule = {
      "@type": "Schedule",
      "repeatFrequency": "P1Y", // Yearly
      "byMonth": getMonthsForTerm(termData.enrollment_data.typically_offered)
    };
  }
  
  // Add workload based on credits
  if (termData.enrollment_data?.credit_count) {
    const [minCredits, maxCredits] = termData.enrollment_data.credit_count;
    const avgCredits = (minCredits + maxCredits) / 2;
    instance.courseWorkload = `PT${avgCredits * 3}H`; // 3 hours per credit per week
  }
  
  // Add instructors
  const termInstructors = termData.enrollment_data?.instructors || {};
  const instructorSchemas: Person[] = Object.entries(termInstructors).map(([name, email]) => {
    const instructorInfo = instructors.find(i => i.name === name);
    return {
      "@type": "Person",
      "name": name,
      "email": email || undefined,
      "url": instructorInfo ? `https://uwcourses.com/instructors/${name.replace(/\s+/g, '_')}` : undefined,
      "worksFor": university
    };
  });
  
  if (instructorSchemas.length > 0) {
    instance.instructor = instructorSchemas;
  }
  
  // Add location (generic for now)
  instance.location = {
    "@type": "Place",
    "name": "University of Wisconsin-Madison",
    "address": {
      "@type": "PostalAddress",
      "addressLocality": "Madison",
      "addressRegion": "WI",
      "postalCode": "53706",
      "addressCountry": "US"
    }
  };
  
  instances.push(instance);
  return instances;
}

function generateOffers(enrollmentData: any): Offer[] {
  return [{
    "@type": "Offer",
    "category": "Paid",
    "availability": enrollmentData?.last_taught_term ? "InStock" : "OutOfStock",
    "price": 0,
    "priceCurrency": "USD",
    "description": "Tuition varies by residency status and credit load. Visit UW-Madison Bursar's office for current rates.",
    "url": "https://bursar.wisc.edu/tuition-and-fees/tuition-rates"
  }];
}

function generateCourseKeywords(course: Course): string {
  const keywords: Set<string> = new Set();
  
  // Add course identifiers
  keywords.add(courseReferenceToString(course.course_reference));
  course.course_reference.subjects.forEach(s => keywords.add(s));
  
  // Add title keywords
  course.course_title.split(/\s+/).forEach(word => {
    if (word.length > 3) keywords.add(word);
  });
  
  // Add level
  const level = getCourseLevel(course.course_reference.course_number);
  keywords.add(level);
  
  // Add UW-specific
  keywords.add("UW-Madison");
  keywords.add("University of Wisconsin");
  
  return Array.from(keywords).join(", ");
}

function getMonthsForTerm(typicallyOffered: string): number[] {
  const termMonths: { [key: string]: number[] } = {
    "Fall": [9, 10, 11, 12],
    "Spring": [1, 2, 3, 4, 5],
    "Summer": [6, 7, 8],
    "Fall and Spring": [1, 2, 3, 4, 5, 9, 10, 11, 12]
  };
  
  return termMonths[typicallyOffered] || [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
}