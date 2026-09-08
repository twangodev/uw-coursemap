<script lang="ts">
  import Page from "../../explorer/[subject]/+page.svelte";
  let { data } = $props();
</script>
<Page {data} />
