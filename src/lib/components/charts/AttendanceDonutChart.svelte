<script lang="ts">

    import {
        type ChartTabularData,
        DonutChart,
        type DonutChartOptions
    } from '@carbon/charts-svelte'
    import '@carbon/charts-svelte/styles.css'
    import type {MandatoryAttendance} from "$lib/types/instructor.ts";

    interface Props {
        attendanceData: MandatoryAttendance | undefined;
    }

    let { attendanceData }: Props = $props();

    let data: ChartTabularData = attendanceData ? [
        {
            group: 'Required',
            value: attendanceData.yes
        },
        {
            group: 'Optional',
            value: attendanceData.no
        },
        {
            group: 'Unknown',
            value: attendanceData.neither
        },
    ] : []

    let options: DonutChartOptions = {
        title: 'Attendance',
        resizable: true,
        donut: {
            center: {
                label: 'Reports',
            },
            alignment: 'center'
        },
        legend: {
            order: ['Required', 'Optional', 'Unknown']
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