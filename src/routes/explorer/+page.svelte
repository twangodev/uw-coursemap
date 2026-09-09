<script lang="ts">
import Directory from "$lib/components/DepartmentDirectory.svelte";
let { data } = $props();
</script>
<Directory {data} map />
