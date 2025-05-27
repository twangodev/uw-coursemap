<script lang="ts">
    import {Card, CardContent, CardHeader, CardTitle} from "$lib/components/ui/card/index.js";
    import {cn} from "$lib/utils.ts";
    import {Change} from "$lib/components/data-card/index.ts";
    import type {Component, SvelteComponent} from "svelte";
    import NumberFlow from "@number-flow/svelte";

    interface Props {
        title: string,
        icon: Component,
        class?: string
        value: number | null,
        suffix?: string
        reference: number | null,
        comparisonKeyword: string,
    }

    let {
        title,
        icon,
        class: className,
        value,
        suffix = '',
        reference,
        comparisonKeyword,
    }: Props = $props();

    let points = $derived.by(() => {
        if (reference !== null && value !== null) {
            return (value - reference) / reference
        }
        return null
    })

    const format: Intl.NumberFormatOptions = {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
    }

</script>

<Card>
    <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle class="text-sm font-medium">{title}</CardTitle>

        {#if icon}
            {@const Icon = icon}
            <Icon class="text-muted-foreground h-4 w-4" />
        {/if}
    </CardHeader>

    <CardContent>
        <div class={cn("text-2xl font-bold", className)}>
            {#if value}
                <NumberFlow {value} {suffix} {format}  />
            {:else }
                Not Reported
            {/if}
        </div>

        <Change
            class="mt-0.5 text-xs"
            {comparisonKeyword}
            {points}
        />
    </CardContent>
</Card>
