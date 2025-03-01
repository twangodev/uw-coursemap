<script lang="ts">
	import ContentWrapper from "$lib/components/content/ContentWrapper.svelte";
    import { Input } from "$lib/components/ui/input/index.ts";
    import { Label } from "$lib/components/ui/label/index.ts";
	import { getDocument, type PDFDocumentProxy } from "pdfjs-dist";
    import "pdfjs-dist/build/pdf.worker.mjs"; // Ensure the worker is bundled

    async function parseDarsPDF(pdfData: ArrayBuffer) {
        const pdf: PDFDocumentProxy = await getDocument({ data: pdfData }).promise;
        let text = "";

        for (let i = 1; i <= pdf.numPages; i++) {
            const page = await pdf.getPage(i);
            const content = await page.getTextContent();
            text += content.items.map((item) => ("str" in item ? item.str : "")).join(" ") + "\n";
        }

        // Get text between "At least {int} Madison credits required" and a lot of "-"s
        const match = text.match(/At least \d+ Madison credits required([\s\S]*?)--------/);

        let output: string;
        if (match) {
            let extractedTextList: Array<string>;
            let extractedTextListOfCourses: Array<Array<string>>;
            
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
            console.log(extractedTextListOfCourses);

            output = "Successfully parsed DARS PDF (I think)";
        } else {
            output = "Error parsing DARS PDF, section used not found";
        }

        // Show output
        console.log(output);
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
    <Label for="dars-upload">Upload DARS PDF:</Label>
    <Input accept="application/pdf" id="dars-upload" type="file" on:change={fileUploaded}/>
</ContentWrapper>
