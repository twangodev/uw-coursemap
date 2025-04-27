<script lang="ts">
    import {type ChartTabularData, ComboChart, type ComboChartOptions, ScaleTypes} from '@carbon/charts-svelte';
    import {calculateGradePointAverage, getTotalOtherGrades} from "$lib/types/madgrades.ts";
    import type {Terms} from "$lib/types/terms.ts";
    import {getCarbonTheme} from "$lib/theme.ts";
    import {mode} from "mode-watcher";
    import type {TermData} from "$lib/types/course.ts";

    const selectedGroups = ['a', 'ab', 'b', 'bc', 'c', 'd', 'f'];
    const selectedGroupsWithOther = selectedGroups.map((group) => group.toUpperCase()).concat(['Other']);

    interface Props {
        term_data: {
            [key: string]: TermData
        };
        terms: Terms;
    }

    let {term_data, terms}: Props = $props();

    function madgradesDataToChartTabularData(termData: { [key: string]: TermData }): ChartTabularData {
        const data: ChartTabularData = [];

        for (const [termCode, value] of Object.entries(termData)) {
            let term = terms[termCode];
            const gradeData = value.grade_data;
            if (!gradeData) {
                continue;
            }
            for (const [grade, count] of Object.entries(gradeData)) {
                if (!selectedGroups.includes(grade)) {
                    continue;
                }
                data.push({
                    group: grade.toUpperCase(),
                    term: term,
                    value: count
                })
            }
            data.push({
                group: 'Other',
                term: term,
                value: getTotalOtherGrades(gradeData)
            })
            data.push({
                group: 'GPA',
                term: term,
                gValue: calculateGradePointAverage(gradeData)
            })
        }
        return data;
    }

    let data: ChartTabularData = $derived(madgradesDataToChartTabularData(term_data));

    let options: ComboChartOptions = $derived({
        title: 'Stacked Grade Distribution + GPA',
        axes: {
            left: {
                title: 'Count',
                stacked: true,
                scaleType: ScaleTypes.LINEAR,
                mapsTo: 'value',
            },
            bottom: {
                title: 'Term',
                scaleType: ScaleTypes.LABELS,
                mapsTo: 'term'
            },
            right: {
                title: 'GPA',
                scaleType: ScaleTypes.LINEAR,
                mapsTo: 'gValue',
                correspondingDatasets: ['GPA'],
                titleOrientation: 'left'
            }
        },
        comboChartTypes: [
            {
                type: 'stacked-area',
                correspondingDatasets: selectedGroupsWithOther
            },
            {
                type: 'line',
                correspondingDatasets: [
                    'GPA'
                ]
            }
        ],
        curve: 'curveMonotoneX',
        height: '500px',
        theme: getCarbonTheme(mode.current)
    })

</script>

<ComboChart {data} {options}/>