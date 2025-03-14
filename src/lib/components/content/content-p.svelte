<script lang="ts">
    interface Props {
        children?: import('svelte').Snippet;
    }

    let { children }: Props = $props();
</script>

<p class="leading-7 not-first:mt-6">
    {@render children?.()}
</p>