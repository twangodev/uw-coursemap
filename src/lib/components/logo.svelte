<script lang="ts">
    import {cn} from "$lib/utils.js";

    const logoPath = '/uw-coursemap-logo.svg';

    interface Props {
        class?: string;
    }

    let { class: className = '' }: Props = $props();
</script>

<div class={cn("flex justify-center items-center w-7 h-auto", className)}>
    <img src={logoPath} alt="Crest"/>
</div>
