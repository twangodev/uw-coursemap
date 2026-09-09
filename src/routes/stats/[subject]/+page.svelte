<script lang="ts">
  import Page from "../../departments/[subject]/+page.svelte";
  let { data } = $props();
</script>
<Page {data} />
