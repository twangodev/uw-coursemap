<script lang="ts">

    interface Props {
        hex: string;
        enabled?: boolean;
        onclick: () => void;
        label?: string;
    }

    let {
        hex,
        enabled,
        onclick,
        label = ""
    }: Props = $props();

</script>
<div class="flex flex-row items-center space-x-2 my-1 {enabled ? 'opacity-100' : 'opacity-50'}">
    <button class="w-4 h-4 rounded-full" aria-label="Show/Hide {label}" style="background-color: {hex}" {onclick}></button>
    <span class="text-sm select-none">{label}</span>
</div>