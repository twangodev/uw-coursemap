<script lang="ts">
  import { departmentName } from "$lib/departments";
  import CourseCollections from "$lib/components/CourseCollections.svelte";
  let { data, map = false }: { data: any; map?: boolean } = $props();
  let query = $state("");
  let departments = $derived(
    data.status.departments.filter((department: any) =>
      `${department.subject} ${departmentName(department.subject)}`
        .toLowerCase()
        .includes(query.trim().toLowerCase()),
    ),
  );
</script>

<div
  class="flex items-center justify-between gap-6 pt-3.5 pb-8 department-heading px-0"
>
  <h1 class="text-[36px]">{map ? "Prerequisite maps" : "Departments"}</h1>
  <label class="sr-only" for="department-query">Find a department</label>
  <input
    class="w-70"
    id="department-query"
    bind:value={query}
    type="search"
    placeholder="Find a department…"
  />
</div>
{#if map}<p class="muted">Explore how courses connect, by department.</p>
  <a href="/explorer/all">Explore all course connections →</a
  >{:else}<CourseCollections />{/if}
<div class="grid grid-cols-4 gap-x-9 department-grid">
  {#each departments as d}<a
      class="flex justify-between gap-3 items-center border-t border-t-border py-6 px-0"
      href={(map ? "/explorer/" : "/departments/") +
        encodeURIComponent(d.subject)}
      ><span class="grid gap-2 leading-[1.4] department-name"
        >{departmentName(d.subject)}<small class="text-[11px] mono muted"
          >{d.subject}</small
        ></span
      ><span class="shrink-0 text-[11px] mono muted">{d.count} courses</span></a
    >{:else}<p class="muted">No matching departments.</p>{/each}
</div>

<style>
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
