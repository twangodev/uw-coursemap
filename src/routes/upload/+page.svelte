<script lang="ts">
  import ContentWrapper from "$lib/components/content/content-wrapper.svelte";
  import { Input } from "$lib/components/ui/input/index.ts";
  import { Label } from "$lib/components/ui/label/index.ts";
  import { Button, buttonVariants } from "$lib/components/ui/button/index.js";
  import { getDocument, type PDFDocumentProxy } from "pdfjs-dist";
  import "pdfjs-dist/build/pdf.worker.mjs"; // Ensure the worker is bundled
  import { getCourse } from "$lib/api.ts";
  import { getData, setData } from "$lib/localStorage.ts";
  import * as Table from "$lib/components/ui/table/index.ts";
  import * as AlertDialog from "$lib/components/ui/alert-dialog/index.js";
  import * as Dialog from "$lib/components/ui/dialog/index.js";
  import { onMount } from "svelte";
  import XMark from "@lucide/svelte/icons/x";
  import CourseSearch from "$lib/components/course-search.svelte";
  import { ChevronDown } from "@lucide/svelte";

  let takenCourses = $state(new Array<any>());
  let status = $state("");
  let browseInput: HTMLInputElement;
  let infoDialogOpen = $state(false);

  //load data
  onMount(() => {
    takenCourses = getData("takenCourses");
  });

  //save the taken courses
  function saveData() {
    setData("takenCourses", takenCourses);
  }

  //used by a button to clear the courses
  function clearCourses(event: Event) {
    //clear
    takenCourses = new Array<any>();
    saveData();

    console.log("Cleared courses");
  }

  //used by a button to remove a course from the list
  function removeCourse(courseToRemove: JSON) {
    for (let i = 0; i < takenCourses.length; i++) {
      if (takenCourses[i]["course_reference"] == courseToRemove) {
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
    let errorCourses: string[] = [];

    //get new courses
    try {
      const pdf: PDFDocumentProxy = await getDocument({ data: pdfData })
        .promise;
      let text: string = "";

      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const content = await page.getTextContent();
        text +=
          content.items
            .map((item) => ("str" in item ? item.str : ""))
            .join(" ") + "\n";
      }

      //get course subject and numbers
      //make sure to keep "-" at the start of the subject search otherwise it will be seen as a range
      const regex = /(\b[-A-Z&]+(?:\s[-A-Z&]+)*\b)\s+(X\d{2}|\d{3})/g;
      let matches,
        results = [];

      while ((matches = regex.exec(text)) !== null) {
        //remove all whitespace
        let courseInfo = matches[0].replace(/\s/g, "");

        //if it has an X, it is a elective
        if (courseInfo.match(/X\d\d/)) {
          continue;
        }

        //get the course's datas
        let courseData = await getCourse(courseInfo);

        //couldnt get course data
        if (courseData == null) {
          errorCourses.push(courseInfo);
          continue;
        }

        //check if it is a duplicate
        let duplicate = false;
        for (let takenCourse of takenCourses) {
          if (
            takenCourse["course_reference"]["course_number"] ==
              courseData["course_reference"]["course_number"] &&
            takenCourse["course_title"] == courseData["course_title"]
          ) {
            console.log("Course is a duplicate:", courseData["course_title"]);
            duplicate = true;
          }
        }

        //add to courses (don't allow duplicates)
        if (!duplicate) {
          takenCourses.push(courseData);
          takenCourses = takenCourses; //force update
          saveData();
        }
      }

      //set status to succes (only if there wasnt an error)
      if (errorCourses.length == 0) {
        status = "";
      } else {
        status =
          "There was an error with " +
          errorCourses.length +
          " course(s).<br>Please submit a bug report if any of these are valid courses, or a part of a valid course:<br>" +
          errorCourses.join("<br>");
      }
    } catch (e) {
      //set status to error
      status =
        "Error parsing pdf, make sure it is a valid unofficial transcript.<br>Please submit and bug report with the error in the console if it is.";
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

    setOpen(false); //close the dialog after file upload
  }

  let myOpen = $state(false);
  function getOpen() {
    return myOpen;
  }

  function setOpen(newOpen: boolean) {
    myOpen = newOpen;
  }
</script>

<ContentWrapper>
  <p class="text-muted-foreground text-base">
    Courses added here will appear as <span class="font-semibold text-green-600"
      >green</span
    > text in the explorer. This is meant to represent courses you've taken.
  </p>
  <p class="text-muted-foreground text-base" style="margin-bottom: 1rem;">
    Courses whose requisites have been taken (but is not a class you've already
    took) will appear as <span class="font-semibold text-yellow-500"
      >yellow</span
    >. This is meant to represent courses you can take next semester.
  </p>

  <div style="margin-bottom: 1rem; display: flex; gap: .5rem;">
    <div style="display: flex;">
      <Dialog.Root bind:open={getOpen, setOpen}>
        <Dialog.Trigger>
          <Button variant="outline">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              class="lucide lucide-upload text-muted-foreground size-7"
              aria-hidden="true"
              style="--darkreader-inline-stroke: currentColor;"
              data-darkreader-inline-stroke=""
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" x2="12" y1="3" y2="15"></line></svg
            >
          </Button>
        </Dialog.Trigger>
        <Dialog.Content>
          <Dialog.Header>
            <Dialog.Title>Upload transcript to add courses:</Dialog.Title>
            <Dialog.Description>
              <div class="grid gap-4 py-4">
                <Button variant="outline" onclick={() => browseInput.click()}
                  >Upload Transcript</Button
                >
                <input
                  bind:this={browseInput}
                  accept="application/pdf"
                  type="file"
                  class="hidden"
                  onchange={fileUploaded}
                />
                <ul style="list-style-type: numbers; margin-left: 20px;">
                  <li>
                    Go to academic records: MyUW -> student center -> academic
                    records
                    <ul style="list-style-type: disc; margin-left: 20px;">
                      <li>
                        Or just go <a
                          style="color: blue; text-decoration: underline;"
                          target="_blank"
                          href="https://madison.sis.wisc.edu/psc/sissso/EMPLOYEE/SA/c/NUI_FRAMEWORK.PT_AGSTARTPAGE_NUI.GBL?CONTEXTIDPARAMS=TEMPLATE_ID%3aPTPPNAVCOL&scname=U__U_ACADEMIC_RECORDS&PTPPB_GROUPLET_ID=U_ACADEMIC_RECORDS&CRefName=U_ACADEMIC_RECORDS"
                          >here</a
                        >
                      </li>
                    </ul>
                  </li>
                  <li>
                    Click on "View Unofficial Transcript" on the left side menu
                  </li>
                  <li>
                    Set "report type" to unofficial transcript, and submit
                  </li>
                  <li>Click on the new transcript, and press "view report"</li>
                  <li>Download the pdf, then upload here</li>
                </ul>
              </div>
            </Dialog.Description>
          </Dialog.Header>
        </Dialog.Content>
      </Dialog.Root>
    </div>

    <div style="width: 100%;">
      <CourseSearch bind:takenCourses bind:status />
    </div>
  </div>

  {#if takenCourses.length == 0 && status == ""}
    <div style="margin-bottom: 1rem;" class="text-muted-foreground text-base">
      Click the upload button to autofill courses, or use the course search to
      manually add courses.
    </div>
  {:else}
    <p>
      {@html status}
    </p>
    <Table.Root id="courses" style="margin-bottom: 1rem;">
      <Table.Header>
        <Table.Row>
          <Table.Head>Remove</Table.Head>
          <Table.Head>Name</Table.Head>
          <Table.Head>Subject(s)</Table.Head>
          <Table.Head>Number</Table.Head>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {#each takenCourses.slice().reverse() as courseData}
          <Table.Row>
            <Table.Cell>
              <Button
                variant="outline"
                size="icon"
                onclick={() => removeCourse(courseData["course_reference"])}
              >
                <XMark class="h-4 w-4" />
              </Button>
            </Table.Cell>
            <Table.Cell>{courseData["course_title"]}</Table.Cell>
            <Table.Cell
              >{courseData["course_reference"]["subjects"].join(
                ", ",
              )}</Table.Cell
            >
            <Table.Cell
              >{courseData["course_reference"]["course_number"]}</Table.Cell
            >
          </Table.Row>
        {/each}
      </Table.Body>
    </Table.Root>
  {/if}

  <AlertDialog.Root>
    <AlertDialog.Trigger>
      <Button variant="destructive">Clear Course Data</Button>
    </AlertDialog.Trigger>
    <AlertDialog.Content>
      <AlertDialog.Header>
        <AlertDialog.Title
          >Are you sure you want to remove all uploaded courses?</AlertDialog.Title
        >
        <AlertDialog.Description>
          This action cannot be undone. This will permanently delete your
          uploaded courses.
        </AlertDialog.Description>
        <AlertDialog.Footer>
          <AlertDialog.Cancel>Cancel</AlertDialog.Cancel>
          <AlertDialog.Cancel onclick={clearCourses}>Clear</AlertDialog.Cancel>
        </AlertDialog.Footer>
      </AlertDialog.Header>
    </AlertDialog.Content>
  </AlertDialog.Root>
</ContentWrapper>
