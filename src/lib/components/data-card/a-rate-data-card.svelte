<script lang="ts">
    import {GenericDataCard} from "$lib/components/data-card/index.js";
    import {BookA} from "@lucide/svelte";

    interface Props {
        termARate: number | null,
        cumulativeARate: number | null,
    }

    let { termARate, cumulativeARate }: Props = $props();

</script>

<GenericDataCard
        title="A Rate"
        icon={BookA}
        value={termARate}
        suffix="%"
        reference={cumulativeARate}
        comparisonKeyword="Historical"
/>