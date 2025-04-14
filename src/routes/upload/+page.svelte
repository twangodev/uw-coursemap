<script lang="ts">
	import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
    import { Input } from "$lib/components/ui/input/index.ts";
    import { Label } from "$lib/components/ui/label/index.ts";
    import {Button, buttonVariants} from "$lib/components/ui/button/index.js";
	import { getDocument, type PDFDocumentProxy } from "pdfjs-dist";
    import "pdfjs-dist/build/pdf.worker.mjs"; // Ensure the worker is bundled
    import {getCourse} from "$lib/api.ts";
    import {getData, setData} from "$lib/localStorage.ts";
    import * as Table from "$lib/components/ui/table/index.ts";
    import * as AlertDialog from "$lib/components/ui/alert-dialog/index.js";
    import { onMount } from 'svelte';
    import XMark from "lucide-svelte/icons/x";
    import CourseSearch from "$lib/components/course-search.svelte";
    
    let takenCourses = $state(new Array<any>)
    let status = $state("");
    let infoDialogOpen = $state(false);
    
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
        let hadError = false;
        
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

                //get the course's datas
                let courseData = await getCourse(courseInfo);
                
                //couldnt get course data
                if(courseData == null){
                    hadError = true;
                    continue;
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

            //set status to succes (only if there wasnt an error)
            if(!hadError){
                status = "";
            }
        }
        catch(e){
            //set status to error
            status = "Error parsing pdf";
            console.error(e);
        }
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
    <div class="space-y-3 mb-8">
        <p class="text-base text-muted-foreground">Courses added here will appear as <span class="text-green-600 font-semibold">green</span> text in the explorer. This is meant to represent courses you've taken.</p>
        <p class="text-base text-muted-foreground">Courses whose requisites have been taken (but is not a class you've already took) will appear as <span class="text-yellow-500 font-semibold">yellow</span>. This is meant to represent courses you can take next semester.
        </p>

        <!-- Add to courses with unofficial transcript -->
            <Label>
                {#if takenCourses.length > 0}
                    Add to courses with 
                    <span
                        class="text-blue-500 underline cursor-pointer"
                        role="button"
                        tabindex="0"
                        onclick={() => infoDialogOpen = true}
                        onkeydown={(e) => e.key === 'Enter' && (infoDialogOpen = true)}
                    >
                        Unofficial Transcript
                    </span>:
                {:else}
                    Upload 
                    <span
                        class="text-blue-500 underline cursor-pointer"
                        role="button"
                        tabindex="0"
                        onclick={() => infoDialogOpen = true}
                        onkeydown={(e) => e.key === 'Enter' && (infoDialogOpen = true)}
                    >
                        Unofficial Transcript
                    </span>:
                {/if}
            </Label>
            
            <div class="flex items-center space-x-4 mt-2">
                <AlertDialog.Root bind:open={infoDialogOpen}>
                    <AlertDialog.Content>
                        <AlertDialog.Header>
                            <AlertDialog.Title>How to get unofficial transcript:</AlertDialog.Title>
                            <AlertDialog.Description>
                                <ul style="list-style-type: disc; margin-left: 20px;">
                                    <li>Go to academic records: MyUW -> student center -> academic records
                                        <ul style="list-style-type: disc; margin-left: 20px;">
                                            <li>Or just go <a style="color: blue; text-decoration: underline;" target="_blank" href="https://madison.sis.wisc.edu/psc/sissso/EMPLOYEE/SA/c/NUI_FRAMEWORK.PT_AGSTARTPAGE_NUI.GBL?CONTEXTIDPARAMS=TEMPLATE_ID%3aPTPPNAVCOL&scname=U__U_ACADEMIC_RECORDS&PTPPB_GROUPLET_ID=U_ACADEMIC_RECORDS&CRefName=U_ACADEMIC_RECORDS">here</a></li>
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
            </div>

        <Input class="max-w-sm" accept="application/pdf" id="transcript-upload" type="file" onchange={fileUploaded} />
        
        <!-- Add to courses with course search -->
        <Label>Or add to courses by searching:</Label>
        <div></div>
        <CourseSearch bind:takenCourses={takenCourses} bind:status={status} defaultString="Add courses..." />
        <div>
            <AlertDialog.Root>
                <AlertDialog.Trigger >
                    <Button variant="destructive">Clear Course Data</Button>
                </AlertDialog.Trigger>
                <AlertDialog.Content>
                    <AlertDialog.Header>
                        <AlertDialog.Title>Are you sure you want to remove all uploaded courses?</AlertDialog.Title>
                        <AlertDialog.Description>
                            This action cannot be undone. This will permanently delete your uploaded courses.
                        </AlertDialog.Description>
                        <AlertDialog.Footer>
                            <AlertDialog.Cancel>
                                Cancel
                            </AlertDialog.Cancel>
                            <AlertDialog.Cancel onclick={clearCourses}>
                                Clear
                            </AlertDialog.Cancel>
                        </AlertDialog.Footer>
                    </AlertDialog.Header>
                </AlertDialog.Content>
            </AlertDialog.Root>

        </div>
    </div>

        
    <Table.Root style="margin-bottom: 20px;">
        {#if takenCourses.length == 0 && status == ""}
            <Table.Caption>no courses to display</Table.Caption>
        {:else}
            <Table.Caption>{status}</Table.Caption>
        {/if}
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
</ContentWrapper>
