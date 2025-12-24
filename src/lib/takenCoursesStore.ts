import { writable, type Writable } from 'svelte/store';
import { browser } from '$app/environment'; // Ensures localStorage is only accessed in the browser
import { getData, setData } from '$lib/localStorage';
import { CourseUtils, type CourseReference } from './types/course';

export const takenCoursesStore: Writable<CourseReference[]> = writable([]);

// Load initial data from localStorage (only in browser)
if (browser) {
  takenCoursesStore.set(getData('takenCourses') || []);
}

// Subscribe to changes and auto-save to localStorage
takenCoursesStore.subscribe((courses) => {
  if (browser) {
    setData('takenCourses', courses);
  }
});

// Helper functions for common operations
export function addCourse(course: CourseReference) {
  takenCoursesStore.update((courses) => {
    // Prevent duplicates
    const isDuplicate = courses.some(
      (taken) =>
        CourseUtils.areEqual(taken, course)
    );
    if (!isDuplicate) {
      return [...courses, course];
    }
    return courses;
  });
}

export function removeCourse(courseReference: CourseReference) {
  takenCoursesStore.update((courses) =>
    courses.filter((course) => !CourseUtils.areEqual(course, courseReference))
  );
}

export function clearCourses() {
  takenCoursesStore.set([]);
}
