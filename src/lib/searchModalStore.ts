import {writable} from "svelte/store";
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
export function allOptionsAreDisabled(options: SearchBarOptions): boolean {
    return !options.showCourses && 
           !options.showDepartments && 
           !options.showInstructors;
};

export const searchModalOpen = writable<boolean>(false);