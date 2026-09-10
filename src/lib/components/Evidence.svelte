<script lang="ts">
  let {
    title,
    files = [],
    description = "",
  }: { title: string; files: string[]; description?: string } = $props();
  let records = $state<any[]>([]);
  let next = $state(0);
  let loading = $state(false);
  let failure = $state("");
  async function load() {
    if (loading || next >= files.length) return;
    loading = true;
    try {
      const r = await fetch(files[next]);
      if (!r.ok)
        throw new Error(
          "Evidence unavailable. Reload to check for a dataset update.",
        );
      records = [...records, ...((await r.json()) as any[])];
      next++;
      failure = "";
    } catch (e) {
      failure = (e as Error).message;
    } finally {
      loading = false;
    }
  }
</script>

<details
  ontoggle={(e) => {
    if (e.currentTarget.open && next === 0) load();
  }}
>
  <summary>{title}</summary>
  <div class="stack">
    {#if description}<p class="muted">
        {description}
      </p>{/if}{#if !files.length}<p class="empty">
        No records available.
      </p>{/if}{#each records as r}<details>
        <summary
          >{r.course_id || r.instructor_name || r.section || "Record"} · {r.observed_at?.slice(
            0,
            10,
          ) ||
            r.created_at?.slice(0, 10) ||
            r.review_date?.slice(0, 10) ||
            r.status ||
            ""}</summary
        >{#if r.title}<h3>{r.title}</h3>{/if}{#if r.description}<p>
            {r.description}
          </p>{/if}{#if r.comment}<p>{r.comment}</p>{/if}
        <details class="raw-record"><summary>Raw record</summary><pre>{JSON.stringify(r, null, 2)}</pre></details>
      </details>{/each}{#if failure}<p role="alert">
        {failure}
      </p>{/if}{#if next < files.length}<button
        onclick={load}
        disabled={loading}
        >{loading
          ? "Loading…"
          : failure
            ? "Retry"
            : "Load more records"}</button
      >{/if}
    <div class="row">
      {#each files as url, i}<a class="mono" href={url} download
          >Download part {i + 1}</a
        >{/each}
    </div>
  </div>
</details>

<style>
  .raw-record { margin-top: 16px; }
  .raw-record summary { color: var(--muted); font-size: 12px; }
  pre { max-height: 360px; overflow: auto; }
</style>
