<script lang="ts">
  import CourseCollectionPage from "$lib/components/CourseCollectionPage.svelte";
  let { data } = $props();
</script>

<CourseCollectionPage {data} />
