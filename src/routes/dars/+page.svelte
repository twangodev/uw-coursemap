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
    
    let coursesFromDars = new Array<any>;
    
    //load data
    onMount(() => {
        coursesFromDars = getData("coursesFromDars");
    });

    function saveData(){
        setData("coursesFromDars", coursesFromDars);
    }

    function clearCourses(event: Event){
        //clear
        coursesFromDars = new Array<any>;
        saveData();

        console.log("Cleared courses")
    }

    async function parseDarsPDF(pdfData: ArrayBuffer) {
        const pdf: PDFDocumentProxy = await getDocument({ data: pdfData }).promise;
        let text: string = "";

        for (let i = 1; i <= pdf.numPages; i++) {
            const page = await pdf.getPage(i);
            const content = await page.getTextContent();
            text += content.items.map((item) => ("str" in item ? item.str : "")).join(" ") + "\n";
        }

        // Get text between "At least {int} Madison credits required" and a lot of "-"s
        const match = text.match(/At least \d+ Madison credits required([\s\S]*?)--------/);

        if (match) {
            let extractedTextListOfCourses: Array<Array<string>>;
            let extractedTextList: Array<string>;
            
            // Get text from match
            let foundText = match[1].trim();

            // Split by semester label + year (space + char + char + int + int + space)
            extractedTextList = foundText.split(/\s[A-Z]{2}\d{2}\s/);

            // Remove first element (not a class)
            extractedTextList = extractedTextList.slice(1);

            // Split individual courses by credits (space + int + . + int + int + space)
            extractedTextListOfCourses = extractedTextList.map(str => str.split(/\s\d\.\d{2}\s/));  

            // Trim each string
            extractedTextListOfCourses = extractedTextListOfCourses.map(list => list.map(str => str.trim()));

            // Get rid of general class name (and trim again)
            extractedTextListOfCourses = extractedTextListOfCourses.map(list => [list[0], list[1].split(" ")[0]]);

            // Condense course IDs (E C E 352 -> ECE352) (COMP SCI300 -> COMPSCI300)
            extractedTextListOfCourses = extractedTextListOfCourses.map(list => [list[0].replace(/ /g, ""), list[1]]);

            // Separate course IDs (ECE352 -> ECE 352) (COMPSCI300 -> COMPSCI 300)
            extractedTextListOfCourses = extractedTextListOfCourses.map(list => [list[0].replace(/([A-Z]+)(\d{3})(.?)/, '$1 $2'), list[1]]);

            // Debug
            console.log(`Courses: ${extractedTextListOfCourses}`);

            //get each course
            for(const courseInfo of extractedTextListOfCourses){
                let courseCode = courseInfo[0];
                
                //get the course's data
                let courseData = await getCourse(courseCode);
                
                //add to courses
                coursesFromDars.push(courseData);
                coursesFromDars = coursesFromDars; //force update
                saveData();
            }
        } else {
            console.log("Error parsing DARS PDF, section used not found");
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
        throw new Error("Could not find course ):");
    }

    async function fileUploaded(event: Event) {
        const target = event.target as HTMLInputElement;
        if (target.files && target.files.length > 0) {
            const file = target.files[0];
            console.log("Uploaded file:", file);
            
            const reader = new FileReader();
            reader.onload = async () => {
                if (reader.result instanceof ArrayBuffer) {
                    await parseDarsPDF(reader.result);
                }
            };
            
            reader.readAsArrayBuffer(file);
        }
    }
</script>

<ContentWrapper>
    {#if coursesFromDars.length > 0}
        <Label for="dars-upload">Add to courses with DARS PDF:</Label>
    {:else}
        <Label for="dars-upload">Upload DARS PDF:</Label>
    {/if}
    <Input accept="application/pdf" id="dars-upload" type="file" on:change={fileUploaded}/>
    
    {#if coursesFromDars.length > 0}
        <Table.Root>
            <Table.Caption>Courses automatically imported from DARS</Table.Caption>
            <Table.Header>
                <Table.Row>
                    <Table.Head>Name</Table.Head>
                    <Table.Head>Subject(s)</Table.Head>
                    <Table.Head>Number</Table.Head>
                </Table.Row>
            </Table.Header>
            <Table.Body>
                {#each coursesFromDars as courseData}
                    <Table.Row>
                        <Table.Cell>{courseData["course_title"]}</Table.Cell>
                        <Table.Cell>{courseData["course_reference"]["subjects"].join(", ")}</Table.Cell>
                        <Table.Cell>{courseData["course_reference"]["course_number"]}</Table.Cell>
                    </Table.Row>
                {/each}
            </Table.Body>
        </Table.Root>  
        <Button variant="destructive" onclick={clearCourses}>Clear Courses</Button>
    {/if}


</ContentWrapper>
