import {PUBLIC_API_URL, PUBLIC_SEARCH_API_URL} from "$env/static/public";

export async function apiFetch(path: string): Promise<Response> {
    return await fetch(`${PUBLIC_API_URL}${path}`);
}

export async function search(query: string): Promise<Response> {
    return await fetch(`${PUBLIC_SEARCH_API_URL}/search`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({"query": query}),
    });
}

export async function getCourse(courseCode: string){
    try{
        //seperate course info
        let section = courseCode.split(" ")[0];
        let number = parseInt(courseCode.split(" ")[1]);

        //get the section data
        const response = await apiFetch(`/courses/${section}.json`)
        let subjectCourses = await response.json();

        //get the specific course
        for(const courseData of subjectCourses){
            if(courseData["course_reference"]["course_number"] == number){
                return courseData;
            }
        }

        //no course found
        throw new Error("Could not find course ):\n" + courseCode);
    }
    catch(e){
        console.log(e);
        return null;
    }
}