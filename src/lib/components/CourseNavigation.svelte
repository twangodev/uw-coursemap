<script lang="ts">
  import { onMount, type Snippet } from "svelte";
  import {
    BookOpen,
    GitBranch,
    CalendarDays,
    Users,
    ChartColumn,
    Layers,
  } from "@lucide/svelte";
  let {
    code,
    title,
    heading,
    content,
    navigationHeight = $bindable(43),
    children,
  }: {
    code: string;
    title: string;
    heading?: HTMLElement;
    content?: HTMLElement;
    navigationHeight?: number;
    children: Snippet;
  } = $props();
  let container: HTMLDivElement;
  let active = $state("overview");
  let stickyTitle = $state(false);
  let sectionNav: HTMLElement;
  let indicator = $state({ left: 0, width: 0 });
  onMount(() => {
    let frame = 0;
    let stopped = false;
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    function update() {
      frame = 0;
      stickyTitle = (heading?.getBoundingClientRect().bottom ?? 1) <= 0;
      const sections = links
        .map((link) => document.getElementById(link.id))
        .filter((el): el is HTMLElement => !!el);
      const threshold = navigationHeight + 64;
      let next = sections[0]?.id || "overview";
      for (const section of sections)
        if (section.getBoundingClientRect().top <= threshold) next = section.id;
      if (
        window.scrollY > 0 &&
        window.scrollY + window.innerHeight >=
          document.documentElement.scrollHeight - 2
      )
        next = sections.at(-1)?.id || next;
      const changed = next !== active;
      active = next;
      const link = sectionNav.querySelector<HTMLAnchorElement>(
        `a[href="#${next}"]`,
      );
      if (!link) return;
      indicator = { left: link.offsetLeft, width: link.offsetWidth };
      // Scroll only the horizontal navigation, never the document.
      if (
        changed &&
        (link.offsetLeft < sectionNav.scrollLeft ||
          link.offsetLeft + link.offsetWidth >
            sectionNav.scrollLeft + sectionNav.clientWidth)
      ) {
        sectionNav.scrollTo({
          left:
            link.offsetLeft - (sectionNav.clientWidth - link.offsetWidth) / 2,
          behavior: motion.matches ? "instant" : "smooth",
        });
      }
    }
    function schedule() {
      if (!frame && !stopped) frame = requestAnimationFrame(update);
    }
    window.addEventListener("scroll", schedule, { passive: true });
    const resize = new ResizeObserver(schedule);
    resize.observe(sectionNav);
    resize.observe(container);
    resize.observe(sectionNav.firstElementChild!);
    if (content) resize.observe(content);
    document.fonts.ready.then(schedule);
    schedule();
    return () => {
      stopped = true;
      cancelAnimationFrame(frame);
      resize.disconnect();
      window.removeEventListener("scroll", schedule);
    };
  });
  const links = [
    { id: "overview", label: "overview", icon: BookOpen },
    { id: "requirements", label: "prerequisites", icon: GitBranch },
    { id: "professors", label: "professors", icon: Users },
    { id: "schedule", label: "calendar", icon: CalendarDays },
    { id: "experience", label: "student experience", icon: BookOpen },
    { id: "grades", label: "grades", icon: ChartColumn },
    { id: "evidence", label: "sources", icon: Layers },
  ];
</script>

<div
  class="course-navigation"
  bind:offsetHeight={navigationHeight}
  bind:this={container}
>
  {#if stickyTitle}<div class="sticky-course-title" aria-hidden="true">
      <span class="sticky-course-code" title={code}>{code}</span><span
        class="sticky-course-name"
        {title}>{title}</span
      >
    </div>{/if}
  <div class="navigation-row">
    <nav
      bind:this={sectionNav}
      class="course-jumps"
      class:has-indicator={indicator.width > 0}
      aria-label="Course sections"
    >
      <div class="section-links">
        {#each links as link}<a
            href={"#" + link.id}
            aria-current={active === link.id ? "location" : undefined}
            ><link.icon size={14} strokeWidth={1.5} />{link.label}</a
          >{/each}
        <span
          class="section-indicator"
          aria-hidden="true"
          style:width={`${indicator.width}px`}
          style:transform={`translateX(${indicator.left}px)`}
        ></span>
      </div>
    </nav>
    <div class="navigation-filters">{@render children()}</div>
  </div>
</div>

<style>
  .course-jumps {
    display: flex;
    gap: 5px;
    overflow-x: auto;
  }
  .course-jumps a {
    display: flex;
    align-items: center;
    white-space: nowrap;
    color: var(--muted);
    font: 14px var(--font-sans);
  }
  .course-jumps a:hover {
    background: var(--surface);
    color: var(--text);
  }
  .course-jumps a[aria-current="location"] {
    color: var(--accent);
  }
  .course-navigation {
    position: sticky;
    top: 0;
    z-index: 20;
    background: var(--bg);
    border-bottom: 1px solid var(--border);
  }
  .navigation-row {
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 6px 0;
  }
  .sticky-course-title {
    display: flex;
    align-items: baseline;
    gap: 12px;
    min-width: 0;
    padding: 10px 8px 4px;
  }
  .sticky-course-code {
    flex-shrink: 0;
    max-width: 45%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--muted);
    font-size: 12px;
  }
  .sticky-course-name {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 15px;
    font-weight: 500;
  }

  .course-navigation .course-jumps {
    position: static;
    flex: 1;
    min-width: 0;
    border: 0;
    margin: 0;
    padding: 0;
  }
  .course-navigation .course-jumps a {
    height: 30px;
    box-sizing: border-box;
    font-size: 12px;
    padding: 0 8px;
    gap: 5px;
  }

  .section-links {
    position: relative;
    display: flex;
    flex: 0 0 auto;
    width: max-content;
    gap: 5px;
  }
  .section-indicator {
    position: absolute;
    left: 0;
    bottom: 0;
    height: 2px;
    background: var(--accent);
    border-radius: 2px;
    pointer-events: none;
    transition:
      transform var(--motion-travel) var(--motion-ease),
      width var(--motion-travel) var(--motion-ease);
  }
  .has-indicator a[aria-current="location"] {
    box-shadow: none;
  }
  @media (prefers-reduced-motion: reduce) {
    .section-indicator {
      transition: none;
    }
  }
  .navigation-filters {
    display: flex;
    gap: 10px;
    flex-shrink: 0;
  }

  @media (max-width: 1000px) {
    .navigation-row {
      flex-wrap: wrap;
      gap: 10px;
    }
    .course-navigation .course-jumps {
      flex-basis: 100%;
    }
    .navigation-filters {
      width: 100%;
    }
  }
</style>
