<script lang="ts">
	import ContentWrapper from "$lib/components/content/ContentWrapper.svelte";
    import { Input } from "$lib/components/ui/input/index.ts";
    import { Label } from "$lib/components/ui/label/index.ts";
    import { Button } from "$lib/components/ui/button/index.js";
	import { getDocument, type PDFDocumentProxy } from "pdfjs-dist";
    import "pdfjs-dist/build/pdf.worker.mjs"; // Ensure the worker is bundled
    import {apiFetch} from "$lib/api.ts";
    import {getData, setData} from "$lib/localStorage.ts";
    import * as Table from "$lib/components/ui/table/index.ts";
    import { onMount } from 'svelte';
    
    let takenCourses = $state(new Array<any>);
    let status = $state("");
    
    //load data
    onMount(() => {
        takenCourses = getData("takenCourses");
    });

    //save the taken courses
    function saveData(){
        setData("takenCourses", takenCourses);
    }

    function clearCourses(event: Event){
        //clear
        takenCourses = new Array<any>;
        saveData();

        console.log("Cleared courses")
    }

    //for unofficial transcript
    async function parseTranscriptPDF(pdfData: ArrayBuffer) {
        //set status to loading
        status = "Loading...";
        
        //get new courses
        try{
            const pdf: PDFDocumentProxy = await getDocument({ data: pdfData }).promise;
            let text: string = "";

            for (let i = 1; i <= pdf.numPages; i++) {
                const page = await pdf.getPage(i);
                const content = await page.getTextContent();
                text += content.items.map((item) => ("str" in item ? item.str : "")).join(" ") + "\n";
            }
            
            //get course subject and numbers
            const regex = /(\b[A-Z]+(?:\s[A-Z]+)*\b)\s+(X\d{2}|\d{3})/g;
            let matches, results = [];
            
            while ((matches = regex.exec(text)) !== null) {
                //remove all whitespace
                let courseInfo = matches[0].replace(/\s/g, "");
                
                let courseData;
                //if it has an there are multiple courses
                if(courseInfo.match(/X\d\d/)){
                    courseData = {
                        "course_title": `Multiple ${courseInfo.split("X")[0]} Courses`,
                        "course_reference": {
                            "subjects": [courseInfo.split("X")[0]],
                            "course_number": "X" + courseInfo.split("X")[1]
                        }
                    }
                }
                else{
                    //split course subject and number
                    courseInfo = courseInfo.replace(/([A-Z]+)(\d{3})(.?)/, '$1 $2')

                    //get the course's data
                    courseData = await getCourse(courseInfo);
                }
                
                //check if it is a duplicate
                let duplicate = false;
                for(let takenCourse of takenCourses){
                    if(
                        takenCourse["course_reference"]["course_number"] == courseData["course_reference"]["course_number"] &&
                        takenCourse["course_title"] == courseData["course_title"]
                    ){
                        console.log("Course is a duplicate:", courseData["course_title"]);
                        duplicate = true;
                    }
                }

                //add to courses (don't allow duplicates)
                if(!duplicate){
                    takenCourses.push(courseData);
                    takenCourses = takenCourses; //force update
                    saveData();
                }
            }
            //set status to succes
            status = "";
        }
        catch(e){
            //set status to error
            status = "There was an error parsing the pdf";
            console.error(e);
        }

    }

    async function getCourse(courseCode: string){
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

    async function fileUploaded(event: Event) {
        const target = event.target as HTMLInputElement;
        if (target.files && target.files.length > 0) {
            const file = target.files[0];
            console.log("Uploaded file:", file);
            
            const reader = new FileReader();
            reader.onload = async () => {
                if (reader.result instanceof ArrayBuffer) {
                    await parseTranscriptPDF(reader.result);
                }
            };
            
            reader.readAsArrayBuffer(file);
        }
    }
</script>

<ContentWrapper>
    <div style="margin-bottom: 2rem;">
        {#if takenCourses.length > 0}
        <Label for="transcript-upload">Add to courses with Unofficial Transcript:</Label>
        {:else}
        <Label for="transcript-upload">Upload Unofficial Transcript:</Label>
        {/if}
        <Input accept="application/pdf" id="transcript-upload" type="file" onchange={fileUploaded}/>
    </div>
    
    {#if takenCourses.length > 0}
        <Table.Root>
            <Table.Caption>{status}</Table.Caption>
            <Table.Header>
                <Table.Row>
                    <Table.Head>Name</Table.Head>
                    <Table.Head>Subject(s)</Table.Head>
                    <Table.Head>Number</Table.Head>
                </Table.Row>
            </Table.Header>
            <Table.Body>
                {#each takenCourses as courseData}
                    <Table.Row>
                        <Table.Cell>{courseData["course_title"]}</Table.Cell>
                        <Table.Cell>{courseData["course_reference"]["subjects"].join(", ")}</Table.Cell>
                        <Table.Cell>{courseData["course_reference"]["course_number"]}</Table.Cell>
                    </Table.Row>
                {/each}
            </Table.Body>
        </Table.Root>
    {/if}
    <Button variant="destructive" onclick={clearCourses}>Clear Course Data</Button>



</ContentWrapper>
