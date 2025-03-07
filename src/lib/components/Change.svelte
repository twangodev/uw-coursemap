<script lang="ts">

    import {MoveRight, TrendingDown, TrendingUp} from "lucide-svelte";
    import {cn} from "$lib/utils.ts";


    const calculateColorFromChange = (points: number | null) => {
        if (points === null || points === 0) {
            return "text-muted-foreground"
        }
        if (points > 0) {
            return "text-green-600 dark:text-green-400"
        } else if (points < 0) {
            return "text-red-600 dark:text-red-400"
        }
    }

    const formatChange = (points: number | null) => {
        if (points === null) {
            return "Could not calculate change"
        }
        const formatted = points.toFixed(2)
        if (points == 0) {
            return `No change from ${comparisonKeyword}`
        }
        return `${Math.abs(points).toFixed(2)}% from ${comparisonKeyword}`
    }

    interface Props {
        class?: string;
        points: number | null;
        comparisonKeyword?: string;
        trendSize?: number;
    }

    let {
        class: className = "",
        points,
        comparisonKeyword = "",
        trendSize = 14
    }: Props = $props();
    

</script>

<p class={cn("flex items-center", className, calculateColorFromChange(points))}>
    <span class="mr-1.5">
        {#if points}
            {#if points > 0}
                <TrendingUp size={trendSize}/>
            {:else if points < 0}
                <TrendingDown size={trendSize}/>
            {:else}
                <MoveRight size={trendSize}/>
            {/if}
        {/if}
    </span>

    {formatChange(points)}
</p>