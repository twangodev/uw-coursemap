<script lang="ts">

    interface Props {
        hex: string;
        onclick: (show: boolean) => void;
        label?: string;
    }

    let {
        hex,
        onclick,
        label = ""
    }: Props = $props();

    let enabled = $state(true);

</script>
<div class="flex flex-row items-center space-x-2 my-1 {enabled ? 'opacity-100' : 'opacity-50'}">
    <button class="w-4 h-4 rounded-full cursor-pointer" aria-label="Show/Hide {label}" style="background-color: {hex}" onclick={() => {
        enabled = !enabled;
        onclick(enabled);
    }}></button>
    <span class="text-sm select-none">{label}</span>
</div>