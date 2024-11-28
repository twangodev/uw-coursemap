<script lang="ts">
    import {cn} from "$lib/utils.js";

    let className = "";

    export {className as class};
</script>

<div class={cn("container px-6 md:px-8 py-8", className)}>
    <slot/>
</div>