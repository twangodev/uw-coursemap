<script lang="ts">
    import {type ChartTabularData, StackedAreaChart, type StackedAreaChartOptions} from '@carbon/charts-svelte';

    let data: ChartTabularData = [
        {group: 'A', value: 1},
        {group: 'B', value: 2},
        {group: 'C', value: 3},
        {group: 'D', value: 4},
        {group: 'E', value: 5},
        {group: 'F', value: 6},
    ]

    let options: StackedAreaChartOptions = {

    }


</script>

<s></s>
<StackedAreaChart {data} {options}/>