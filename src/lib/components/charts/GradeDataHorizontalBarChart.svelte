<script lang="ts">

    import {getTotalOtherGrades, type MadgradesData} from "$lib/types/madgrades.ts";
    import {type BarChartOptions, BarChartSimple, type ChartTabularData, ScaleTypes} from '@carbon/charts-svelte'
    import '@carbon/charts-svelte/styles.css'

    interface Props {
        madgradesData: MadgradesData;
        term?: string | null;
    }

    let { madgradesData, term = null }: Props = $props();

    let gradeData = term ? madgradesData.by_term[term] : madgradesData.cumulative
    let data: ChartTabularData = [
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
    ].reverse()

    let options: BarChartOptions = {
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
    }

</script>

<div class="h-full">
    <BarChartSimple {data} {options} class="h-full"/>
</div>