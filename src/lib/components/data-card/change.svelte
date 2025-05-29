<script lang="ts">

    import {MoveRight, TrendingDown, TrendingUp} from "@lucide/svelte";
    import {cn} from "$lib/utils.ts";
    import NumberFlow from "@number-flow/svelte";

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

    const percentFormat: Intl.NumberFormatOptions = {
        style: "percent",
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
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

    {#if points !== null}
        {#if points}
            <NumberFlow value={points} suffix=" " format={percentFormat}/>
            <span class="line-clamp-1 break-all overflow-ellipsis">from {comparisonKeyword}</span>
        {:else}
            No change from {comparisonKeyword}
        {/if}
    {:else}
         Could not calculate change
    {/if}
</p>