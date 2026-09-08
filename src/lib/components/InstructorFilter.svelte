<script lang="ts">
  import { onDestroy } from "svelte";
  let {
    value = $bindable(""),
    revision,
    onchange,
  }: { value?: string; revision: string; onchange: () => void } = $props();
  let text = $state("");
  let matches = $state<
    { instructor_uid: string; name: string; current: boolean }[]
  >([]);
  let failure = $state("");
  let timer: ReturnType<typeof setTimeout>;
  let controller: AbortController | undefined;
  function suggest() {
    clearTimeout(timer);
    controller?.abort();
    if (text.trim().length < 2) {
      matches = [];
      return;
    }
    timer = setTimeout(async () => {
      controller = new AbortController();
      try {
        const p = new URLSearchParams({
          kind: "instructor",
          q: text,
          revision,
        });
        const r = await fetch("/api/search?" + p, {
          signal: controller.signal,
        });
        if (!r.ok) throw new Error("Instructor search unavailable.");
        const result = (await r.json()) as { items: typeof matches };
        matches = result.items.slice(0, 8);
        failure = "";
      } catch (e) {
        if ((e as Error).name !== "AbortError") failure = (e as Error).message;
      }
    }, 200);
  }
  function choose(uid: string, name: string) {
    value = uid;
    text = name;
    matches = [];
    onchange();
  }
  onDestroy(() => {
    clearTimeout(timer);
    controller?.abort();
  });
</script>

<div class="picker">
  <label
    >Instructor<input
      aria-label="Filter by instructor"
      bind:value={text}
      oninput={suggest}
      placeholder={value ? "Instructor selected" : "Type a name…"}
      autocomplete="off"
    /></label
  ><input type="hidden" name="instructor" {value} />{#if value}<button
      type="button"
      class="clear"
      onclick={() => choose("", "")}>Clear instructor</button
    >{/if}{#if matches.length}<ul aria-label="Matching instructors">
      {#each matches as i}<li>
          <button type="button" onclick={() => choose(i.instructor_uid, i.name)}
            >{i.name}{i.current ? " · current" : ""}</button
          >
        </li>{/each}
    </ul>{/if}{#if failure}<p role="alert">{failure}</p>{/if}
</div>

<style>
  .picker {
    position: relative;
  }
  .picker label {
    display: grid;
    gap: 0.3rem;
    font-size: 0.8rem;
    color: var(--muted);
  }
  .picker input {
    width: 200px;
  }
  ul {
    position: absolute;
    top: 100%;
    left: 0;
    z-index: 10;
    list-style: none;
    padding: 0.4rem;
    border: 1px solid var(--border);
    background: var(--bg);
    min-width: 270px;
    box-shadow: 0 8px 24px #0001;
  }
  li button {
    border: 0;
    width: 100%;
    text-align: left;
    font-size: 0.85rem;
  }
  .clear {
    border: 0;
    padding: 0.2rem 0;
    font-size: 0.75rem;
    color: var(--accent);
  }
</style>
