<script lang="ts">

    import {getTotalOtherGrades, type GradeData} from "$lib/types/madgrades.ts";
    import {type BarChartOptions, BarChartSimple, type ChartTabularData, ScaleTypes} from '@carbon/charts-svelte'
    import '@carbon/charts-svelte/styles.css'
    import {getCarbonTheme} from "$lib/theme.ts";
    import {mode} from "mode-watcher";
    import type {TermData} from "$lib/types/course.ts";

    interface Props {
        cumulative: GradeData,
        termData: {
            [key: string]: TermData
        },
        term?: string | null;
    }

    let {
        cumulative,
        termData,
        term = null
    }: Props = $props();

    let gradeData = term ? (termData[term].grade_data ?? cumulative) : cumulative
    let data: ChartTabularData = $derived([
        {
            group: 'A',
            value: gradeData.a
        },
        {
            group: 'AB',
            value: gradeData.ab
        },
        {
            group: 'B',
            value: gradeData.b
        },
        {
            group: 'BC',
            value: gradeData.bc
        },
        {
            group: 'C',
            value: gradeData.c
        },
        {
            group: 'D',
            value: gradeData.d
        },
        {
            group: 'F',
            value: gradeData.f
        },
        {
            group: 'Other',
            value: getTotalOtherGrades(gradeData),
        }
    ].reverse())

    let options: BarChartOptions = $derived({
        title: 'Grade Distribution',
        axes: {
            left: {
                mapsTo: 'group',
                scaleType: ScaleTypes.LABELS,
            },
            bottom: {
                mapsTo: 'value'
            }
        },
        legend: {
            order: [
                'A',
                'AB',
                'B',
                'BC',
                'C',
                'D',
                'F'
            ]
        },
        toolbar: {
            enabled: false
        },
        theme: getCarbonTheme($mode)
    })

</script>

<div class="h-full">
    <BarChartSimple {data} {options} class="h-full"/>
</div>