<script lang="ts">
  let { data } = $props();
</script>

<svelte:head><title>Departments · UW Courses</title></svelte:head>
<div class="hero">
  <p class="eyebrow">Explore the catalog</p>
  <h1>Departments</h1>
</div>
<div class="grid">
  {#each data.status.departments as d}<a
      class="row between section"
      href={"/subjects/" + encodeURIComponent(d.subject)}
      >{d.subject}<span class="mono muted">{d.count} courses</span></a
    >{/each}
</div>
