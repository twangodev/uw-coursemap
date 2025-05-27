<script lang="ts">
    import {GenericDataCard} from "$lib/components/data-card/index.js";
    import {CircleCheckBig} from "@lucide/svelte";

    interface Props {
        termCompletionRate: number | null,
        cumulativeCompletionRate: number | null,
    }

    let { termCompletionRate, cumulativeCompletionRate }: Props = $props();

</script>

<GenericDataCard
        title="Completion Rate"
        icon={CircleCheckBig}
        value={termCompletionRate}
        suffix="%"
        reference={cumulativeCompletionRate}
        comparisonKeyword="Historical"
/>