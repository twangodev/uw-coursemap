<script lang="ts">
    import {type ChartTabularData, ComboChart, type ComboChartOptions, ScaleTypes} from '@carbon/charts-svelte';
    import {calculateGradePointAverage, getTotalOtherGrades, type MadgradesData} from "$lib/types/madgrades.ts";
    import type {Terms} from "$lib/types/terms.ts";

    const selectedGroups = ['a', 'ab', 'b', 'bc', 'c', 'd', 'f'];
    const selectedGroupsWithOther = selectedGroups.map((group) => group.toUpperCase()).concat(['Other']);

    interface Props {
        madgradesData: MadgradesData;
        terms: Terms;
    }

    let { madgradesData, terms }: Props = $props();

    function madgradesDataToChartTabularData(madgradesData: MadgradesData): ChartTabularData {
        const data: ChartTabularData = [];

        for (const [termCode, value] of Object.entries(madgradesData.by_term)) {
            let term = terms[termCode];
            for (const [grade, count] of Object.entries(value)) {
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
                value: getTotalOtherGrades(value)
            })
            data.push({
                group: 'GPA',
                term: term,
                gValue: calculateGradePointAverage(value)
            })
        }
        return data;
    }

    let data: ChartTabularData = $derived(madgradesDataToChartTabularData(madgradesData));

    let options: ComboChartOptions = {
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
        height: '500px'
    }

</script>

<ComboChart {data} {options}/>