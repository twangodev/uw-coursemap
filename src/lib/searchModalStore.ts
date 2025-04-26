import {writable} from "svelte/store";
import { Book, School, User } from '@lucide/svelte';
import type { Icon } from '@lucide/svelte';
import type { Component, ComponentType } from 'svelte';

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
    // TODO: Update lucide-svelte to use Component instead of ComponentType<Icon>
    // I suspect lucide-svelte is written for Svelte 4, not Svelte 5 so its component
    // type is not compatible with Svelte 5's component type
    icon?: Component | ComponentType<Icon>; 
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