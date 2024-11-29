<script lang="ts">

    import type {MadgradesData} from "$lib/types/madgrades.ts";
    import {BarChartSimple, ScaleTypes} from '@carbon/charts-svelte'
    import '@carbon/charts-svelte/styles.css'

    export let madgradesData: MadgradesData;
    export let term: string | null = null;

    let gradeData = term ? madgradesData.by_term[term] : madgradesData.cumulative
    let data = [
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
        }
    ].reverse()

    let options = {
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
        }
    }

</script>

<div class="h-full">
    <BarChartSimple {data} {options} class="h-full"/>
</div>