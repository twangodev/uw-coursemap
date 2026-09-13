<script lang="ts">
  import { safeUrl } from "$lib/format";
  let {
    title,
    files = [],
    description = "",
    downloadOnly = false,
  }: {
    title: string;
    files: string[];
    description?: string;
    downloadOnly?: boolean;
  } = $props();
  let records = $state<any[]>([]);
  let next = $state(0);
  let visible = $state(8);
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
    if (e.currentTarget.open && next === 0 && !downloadOnly) load();
  }}
>
  <summary>{title}</summary>
  <div class="stack">
    {#if description}<p class="muted">
        {description}
      </p>{/if}{#if !files.length}<p class="empty">
        No records available.
      </p>{/if}{#each records.slice(0, visible) as r}<details>
        <summary
          >{r.instructor_name || r.course_id || r.section || "Record"} · {r.review_date?.slice(
            0,
            10,
          ) ||
            r.observed_at?.slice(0, 10) ||
            r.created_at?.slice(0, 10) ||
            r.review_date?.slice(0, 10) ||
            r.status ||
            ""}</summary
        >{#if r.title}<h3>{r.title}</h3>{/if}{#if r.description}<p>
            {r.description}
          </p>{/if}{#if r.comment}<blockquote
            class="text-[14px] leading-[1.7] whitespace-pre-line wrap-anywhere my-4 mx-0"
          >
            {r.comment}
          </blockquote>{/if}
        {#if safeUrl(r.source_url)}<a
            href={safeUrl(r.source_url)}
            target="_blank"
            rel="noreferrer">View original source ↗</a
          >{/if}
        <details class="mt-4 raw-record">
          <summary class="text-muted text-[12px]">Raw record</summary>
          <pre class="max-h-90 overflow-auto">{JSON.stringify(r, null, 2)}</pre>
        </details>
      </details>{/each}{#if failure}<p role="alert">
        {failure}
      </p>{/if}{#if records.length > visible}<button
        onclick={() => (visible += 8)}>Show more records</button
      >{:else if !downloadOnly && next < files.length}<button
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
