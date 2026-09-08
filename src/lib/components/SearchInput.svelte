<script lang="ts">
  import { untrack } from "svelte";
  import { goto } from "$app/navigation";
  import type { CourseCard } from "$lib/types";

  let {
    value = "",
    revision,
    filters = {},
    label = "Search courses",
    placeholder = "A course or topic…",
  }: {
    value?: string;
    revision: string;
    filters?: Record<string, string>;
    label?: string;
    placeholder?: string;
  } = $props();
  const id = $props.id();
  let query = $state(untrack(() => value));
  let focused = $state(false);
  let dismissed = $state(false);
  let items = $state<CourseCard[]>([]);
  let active = $state(-1);
  let message = $state("");
  let pending = $state(false);
  let open = $derived(focused && !dismissed && query.trim().length >= 2);
  $effect(() => {
    query = value;
  });
  $effect(() => {
    const text = query.trim();
    const params = new URLSearchParams({
      ...filters,
      q: text,
      revision,
      kind: "course",
    });
    params.delete("page");
    params.delete("sort");
    items = [];
    active = -1;
    message = "";
    if (!open) {
      pending = false;
      return;
    }
    pending = true;
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        const response = await fetch(`/api/search?${params}`, {
          signal: controller.signal,
        });
        if (!response.ok) throw new Error("Search unavailable");
        const data = (await response.json()) as { items: CourseCard[] };
        if (controller.signal.aborted) return;
        items = data.items.slice(0, 6);
        message = items.length
          ? `${items.length} suggestions available`
          : "No matching courses. Try another search.";
      } catch {
        if (!controller.signal.aborted)
          message = "Suggestions unavailable. Press Enter to search.";
      } finally {
        if (!controller.signal.aborted) pending = false;
      }
    }, 180);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  });
  function choose(item: CourseCard) {
    dismissed = true;
    goto(`/courses/${item.course_uid}`);
  }
  function keydown(event: KeyboardEvent) {
    if (event.key === "Escape") {
      dismissed = true;
      active = -1;
      return;
    }
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      dismissed = false;
      if (items.length)
        active =
          (active +
            (event.key === "ArrowDown" ? 1 : active < 0 ? 0 : -1) +
            items.length) %
          items.length;
    } else if (event.key === "Enter" && open && active >= 0 && items[active]) {
      event.preventDefault();
      choose(items[active]);
    }
  }
</script>

<div class="search-input">
  <input
    name="q"
    bind:value={query}
    aria-label={label}
    {placeholder}
    maxlength="200"
    role="combobox"
    aria-autocomplete="list"
    aria-expanded={open}
    aria-controls={`${id}-suggestions`}
    aria-activedescendant={open && active >= 0 ? `${id}-${active}` : undefined}
    autocomplete="off"
    onfocus={() => {
      focused = true;
    }}
    onblur={() => {
      focused = false;
    }}
    oninput={() => {
      dismissed = false;
    }}
    onkeydown={keydown}
  />
  <span class="sr-only" role="status">{pending ? "Searching…" : message}</span>
  {#if open}
    <div class="suggestions">
      <ul
        id={`${id}-suggestions`}
        role="listbox"
        aria-label="Suggested courses"
        aria-busy={pending}
      >
        {#each items as item, index (item.course_uid)}
          <li
            id={`${id}-${index}`}
            role="option"
            aria-selected={active === index}
          >
            <button
              type="button"
              tabindex="-1"
              onpointerdown={(event) => event.preventDefault()}
              onclick={() => choose(item)}
            >
              <strong>{item.course_id}</strong><span>{item.title}</span>
            </button>
          </li>
        {/each}
      </ul>
      {#if pending || !items.length}<p>
          {pending ? "Searching…" : message}
        </p>{:else}<p>↑ ↓ to choose · Enter to open</p>{/if}
    </div>
  {/if}
</div>

<style>
  .search-input {
    position: relative;
    flex: 1;
    min-width: 0;
  }
  input {
    width: 100%;
    min-width: 0;
    padding: 10px 0;
    border: 0;
    background: transparent;
    color: var(--text);
    font: inherit;
  }
  input:focus-visible {
    outline: none;
  }
  .search-input:focus-within {
    box-shadow: 0 1px var(--accent);
  }
  .suggestions {
    position: absolute;
    z-index: 50;
    top: calc(100% + 12px);
    left: 0;
    right: 0;
    min-width: min(320px, 75vw);
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--bg);
    box-shadow: 0 12px 28px #00000012;
    overflow: hidden;
  }
  ul {
    list-style: none;
    margin: 0;
    padding: 6px;
  }
  button {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 3px;
    width: 100%;
    padding: 12px;
    text-align: left;
    border: 0;
    background: transparent;
    color: var(--text);
    border-radius: 3px;
    font: inherit;
  }
  button:hover,
  li[aria-selected="true"] button {
    background: var(--surface);
  }
  strong {
    font-size: 13px;
    font-weight: 600;
  }
  button span {
    font-size: 13px;
    color: var(--muted);
  }
  p {
    margin: 0;
    padding: 10px 18px;
    color: var(--muted);
    font-size: 11px;
    border-top: 1px solid var(--border);
  }
</style>
