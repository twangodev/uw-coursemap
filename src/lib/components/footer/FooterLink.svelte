<script>
    export let href = '';
    export let target = '_blank';
    export let className = "font-medium underline underline-offset-4"
</script>

<a href="{href}" target="{target}" class="{className}">
    <slot/>
</a>