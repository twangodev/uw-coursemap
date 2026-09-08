<script lang="ts">
  let { data } = $props();
  let query = $state("");
  let departments = $derived(
    data.status.departments.filter((department) =>
      department.subject.toLowerCase().includes(query.trim().toLowerCase()),
    ),
  );
</script>

<svelte:head><title>Departments · UW Courses</title></svelte:head>
<div class="department-heading">
  <h1>Departments</h1>
  <label class="sr-only" for="department-query">Find a department</label>
  <input
    id="department-query"
    bind:value={query}
    type="search"
    placeholder="Find a department…"
  />
</div>
<div class="department-grid">
  {#each departments as d}<a href={"/subjects/" + encodeURIComponent(d.subject)}
      ><span>{d.subject}</span><span class="mono muted">{d.count} courses</span
      ></a
    >{:else}<p class="muted">No matching departments.</p>{/each}
</div>

<style>
  .department-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    padding: 14px 0 32px;
  }
  h1 {
    font-size: 36px;
  }
  input {
    width: 280px;
  }
  .department-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    column-gap: 36px;
  }
  .department-grid a {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: center;
    padding: 24px 0;
    border-top: 1px solid var(--border);
  }
  @media (max-width: 900px) {
    .department-grid {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
  }
  @media (max-width: 640px) {
    .department-heading {
      align-items: start;
      flex-direction: column;
      gap: 20px;
    }
    input {
      width: 100%;
    }
    .department-grid {
      grid-template-columns: 1fr 1fr;
      column-gap: 24px;
    }
    .department-grid a {
      align-items: start;
      flex-direction: column;
      gap: 4px;
      padding: 18px 0;
    }
  }
</style>
