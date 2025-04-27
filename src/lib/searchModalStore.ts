import {writable} from "svelte/store";
import type { Component } from 'svelte';
import {Book, School, User} from "@lucide/svelte";

export interface SearchBarOptions {
    showCourses: boolean;
    showDepartments: boolean;
    showInstructors: boolean;
}

export const searchOptions = writable<SearchBarOptions>({
    showCourses: true,
    showDepartments: true,
    showInstructors: true,
})

export function setSearchFilters(enabledFilters: (keyof SearchBarOptions)[]) {
    searchOptions.update(current => {
        const newOptions = { ...current };
        // First, set all options to false
        (Object.keys(current) as (keyof SearchBarOptions)[]).forEach(key => {
            newOptions[key] = false;
        });
        // Then enable only the specified filters
        enabledFilters.forEach(filter => {
            newOptions[filter] = true;
        });
        return newOptions;
    });
}

export function allOptionsAreDisabled(options: SearchBarOptions): boolean {
    return !options.showCourses && 
           !options.showDepartments && 
           !options.showInstructors;
};

export interface FilterOptionDisplay {
    id: keyof SearchBarOptions;
    label: string;
    icon?: Component;
}

export const filterOptions: FilterOptionDisplay[] = [
    {
        id: 'showCourses',
        label: 'Courses',
        icon: Book 
    },
    {
        id: 'showDepartments',
        label: 'Departments',
        icon: School
    },
    {
        id: 'showInstructors',
        label: 'Instructors',
        icon: User
    }
];

export const searchModalOpen = writable<boolean>(false);