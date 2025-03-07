<script lang="ts">

    import {type ChartTabularData, WordCloudChart, type WordCloudChartOptions} from '@carbon/charts-svelte'
    import { removeStopwords, eng } from 'stopword'
    import '@carbon/charts-svelte/styles.css'
    import type {FullInstructorInformation} from "$lib/types/instructor.ts";

    interface Props {
        instructors: FullInstructorInformation[];
    }

    let { instructors }: Props = $props();

    function commentsToChartTabularData(instructors: FullInstructorInformation[]): ChartTabularData {
        const wordCounts = new Map();

        // Helper function to process a single comment and count words
        function processComment(comment: string, instructorName: string) {
            // Normalize comment by removing punctuation and converting to lowercase
            const normalized = comment.replace(/[^a-zA-Z0-9\s]/g, '').toLowerCase();
            // Split comment into words
            const words = removeStopwords(normalized.split(/\s+/));
            // Count each word and associate it with the instructor's name
            words.forEach(word => {
                if (word) { // Ignore empty strings
                    if (!wordCounts.has(word)) {
                        wordCounts.set(word, new Map());
                    }
                    const instructorCounts = wordCounts.get(word);
                    instructorCounts.set(instructorName, (instructorCounts.get(instructorName) || 0) + 1);
                }
            });
        }

        // Iterate over instructors and process their comments
        instructors.forEach(instructor => {
            if (instructor.rmp_data && instructor.rmp_data.ratings) {
                instructor.rmp_data.ratings.forEach(rating => {
                    processComment(rating.comment, instructor.name);
                });
            }
        });

        // Convert the wordCounts map to an array of objects for tabular data
        const tabularData: ChartTabularData = [];
        wordCounts.forEach((instructorCounts, word) => {
            instructorCounts.forEach((count: number, instructorName: string) => {
                tabularData.push({ word, value: count, group: instructorName });
            });
        });

        return tabularData;
    }


    let data: ChartTabularData = $derived(commentsToChartTabularData(instructors));
    

    let options: WordCloudChartOptions = {
        title: 'Word Cloud',
        resizable: true,
        height: '400px'
    }


</script>

<div class="h-full">
    <WordCloudChart {data} {options} class="py-4" />
</div>