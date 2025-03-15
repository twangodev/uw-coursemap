<script lang="ts">
	import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
    import { Input } from "$lib/components/ui/input/index.ts";
    import { Label } from "$lib/components/ui/label/index.ts";
    import {Button, buttonVariants} from "$lib/components/ui/button/index.js";
	import { getDocument, type PDFDocumentProxy } from "pdfjs-dist";
    import "pdfjs-dist/build/pdf.worker.mjs"; // Ensure the worker is bundled
    import {apiFetch} from "$lib/api.ts";
    import {getData, setData} from "$lib/localStorage.ts";
    import * as Table from "$lib/components/ui/table/index.ts";
    import * as AlertDialog from "$lib/components/ui/alert-dialog/index.js";
    import { onMount } from 'svelte';
    import XMark from "lucide-svelte/icons/x";
    
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

    //used by a button to clear the courses
    function clearCourses(event: Event){
        //clear
        takenCourses = new Array<any>;
        saveData();

        console.log("Cleared courses")
    }

    //used by a button to remove a course from the list
    function removeCourse(courseToRemove: JSON){
        for(let i = 0; i < takenCourses.length; i++){
            if(takenCourses[i]["course_reference"] == courseToRemove){
                takenCourses.splice(i, 1);
                takenCourses = takenCourses; //force update
                saveData();
                return;
            }
        }
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
                
                //if it has an X, it is a elective
                if(courseInfo.match(/X\d\d/)){
                    continue;
                }

                //split course subject and number
                courseInfo = courseInfo.replace(/([A-Z]+)(\d{3})(.?)/, '$1 $2')

                //get the course's data
                let courseData = await getCourse(courseInfo);
                
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
        <div style="display: flex;">
            <AlertDialog.Root>
                <AlertDialog.Trigger >
                    <Button variant="outline">Info</Button>
                </AlertDialog.Trigger>
                <AlertDialog.Content>
                    <AlertDialog.Header>
                        <AlertDialog.Title>How to get unofficial transcript:</AlertDialog.Title>
                        <AlertDialog.Description>
                            <ul style="list-style-type: disc; margin-left: 20px;">
                                <li>Go to academic records: MyUW -> student center -> academic records
                                    <ul style="list-style-type: disc; margin-left: 20px;">
                                        <li>Or just go <a style="color: blue; text-decoration: underline;" href="https://madison.sis.wisc.edu/psc/sissso/EMPLOYEE/SA/c/NUI_FRAMEWORK.PT_AGSTARTPAGE_NUI.GBL?CONTEXTIDPARAMS=TEMPLATE_ID%3aPTPPNAVCOL&scname=U__U_ACADEMIC_RECORDS&PTPPB_GROUPLET_ID=U_ACADEMIC_RECORDS&CRefName=U_ACADEMIC_RECORDS">here</a></li>
                                    </ul>
                                </li>
                                <li>Click on "View Unofficial Transcript on the side menu"</li>
                                <li>Set "report type" to unofficial transcript, and submit</li>
                                <li>Click on the new transcript, and press "view report"</li>
                                <li>Download the pdf</li>
                                <li>Upload using the file browser on this page</li>
                            </ul>
                        </AlertDialog.Description>
                    </AlertDialog.Header>
                    <AlertDialog.Footer>
                        <AlertDialog.Cancel>Close</AlertDialog.Cancel>
                    </AlertDialog.Footer>
                </AlertDialog.Content>
            </AlertDialog.Root>
            <Input accept="application/pdf" id="transcript-upload" type="file" onchange={fileUploaded}/>
        </div>
    </div>
    
    {#if takenCourses.length > 0}
        <Table.Root>
            <Table.Caption>{status}</Table.Caption>
            <Table.Header>
                <Table.Row>
                    <Table.Head>Remove</Table.Head>
                    <Table.Head>Name</Table.Head>
                    <Table.Head>Subject(s)</Table.Head>
                    <Table.Head>Number</Table.Head>
                </Table.Row>
            </Table.Header>
            <Table.Body>
                {#each takenCourses as courseData}
                    <Table.Row>
                        <Table.Cell>
                            <Button variant="outline" size="icon" onclick={() => removeCourse(courseData["course_reference"])}>
                                <XMark class="h-4 w-4" />
                            </Button>
                        </Table.Cell>
                        <Table.Cell>{courseData["course_title"]}</Table.Cell>
                        <Table.Cell>{courseData["course_reference"]["subjects"].join(", ")}</Table.Cell>
                        <Table.Cell>{courseData["course_reference"]["course_number"]}</Table.Cell>
                    </Table.Row>
                {/each}
            </Table.Body>
        </Table.Root>
    {/if}

    <AlertDialog.Root>
        <AlertDialog.Trigger >
            <Button variant="destructive">Clear Course Data</Button>
        </AlertDialog.Trigger>
        <AlertDialog.Content>
            <AlertDialog.Header>
                <AlertDialog.Title>Are you sure you want to remove all uploaded courses?</AlertDialog.Title>
                <AlertDialog.Footer>
                    <AlertDialog.Cancel>
                        <Button variant="soft" color="gray">
                            Cancel
                        </Button>
                    </AlertDialog.Cancel>
                    <AlertDialog.Cancel>
                        <Button variant="solid" color="red" onclick={clearCourses}>
                            Revoke access
                        </Button>
                    </AlertDialog.Cancel>
                </AlertDialog.Footer>
            </AlertDialog.Header>
        </AlertDialog.Content>
    </AlertDialog.Root>
    
</ContentWrapper>
