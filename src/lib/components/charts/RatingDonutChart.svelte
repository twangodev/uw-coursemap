<script lang="ts">

    import {
        type ChartTabularData,
        DonutChart,
        type DonutChartOptions
    } from '@carbon/charts-svelte'
    import '@carbon/charts-svelte/styles.css'
    import type {RatingsDistribution} from "$lib/types/instructor.ts";

    interface Props {
        ratingData: RatingsDistribution | undefined;
    }

    let { ratingData }: Props = $props();

    let data: ChartTabularData = $derived(ratingData ? [
        {
            group: '1 Star',
            value: ratingData.r1
        },
        {
            group: '2 Stars',
            value: ratingData.r2
        },
        {
            group: '3 Stars',
            value: ratingData.r3
        },
        {
            group: '4 Stars',
            value: ratingData.r4
        },
        {
            group: '5 Stars',
            value: ratingData.r5
        },
    ] : [])

    let options: DonutChartOptions = {
        title: 'Ratings',
        resizable: true,
        donut: {
            center: {
                label: 'Comments',
            },
            alignment: 'center'
        },
        legend: {
            order: ['1 Star', '2 Stars', '3 Stars', '4 Stars', '5 Stars']
        },
        height: '350px',
        toolbar: {
            enabled: false
        }
    }

</script>

<div class="h-full">
    <DonutChart {data} {options} class="h-full"/>
</div>