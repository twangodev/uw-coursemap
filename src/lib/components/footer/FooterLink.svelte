<script>
    export let href = '';
    export let target = '_blank';
    export let class_ = "font-medium underline underline-offset-4"
</script>

<a href="{href}" target="{target}" class="{class_}">
    <slot/>
</a>