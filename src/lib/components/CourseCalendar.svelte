<script lang="ts">
  import { onMount } from "svelte";
  import {
    ChevronLeft,
    ChevronRight,
    Download,
    X,
    MapPin,
    Users,
  } from "@lucide/svelte";
  import {
    localTime,
    monday,
    addDays,
    dayLabel,
    sectionName,
    timeLabel,
    placeMeetings,
    type Meeting,
  } from "$lib/calendar";
  let { files, observedAt }: { files: string[]; observedAt: string } = $props();
  let host: HTMLDivElement;
  let meetings = $state<Meeting[]>([]),
    loading = $state(false),
    loaded = $state(false),
    failure = $state("");
  let week = $state(""),
    section = $state(""),
    selected = $state<Meeting | null>(null);
  const controller = new AbortController();
  let filtered = $derived(
    meetings.filter((m) => !section || sectionName(m.name) === section),
  );
  let days = $derived(
    week ? Array.from({ length: 7 }, (_, i) => addDays(week, i)) : [],
  );
  let visible = $derived(
    filtered.filter((m) => days.includes(localTime(m.starts_at).date)),
  );
  let weekend = $derived(
    visible.some((m) => days.indexOf(localTime(m.starts_at).date) > 4),
  );
  let shownDays = $derived(days.slice(0, weekend ? 7 : 5));
  let startHour = $derived(
    Math.min(
      8,
      ...visible.map((m) => Math.floor(localTime(m.starts_at).minute / 60)),
    ),
  );
  let endHour = $derived(
    Math.max(
      18,
      ...visible.map((m) => Math.ceil(localTime(m.ends_at).minute / 60)),
    ),
  );
  let hours = $derived(
    Array.from({ length: endHour - startHour }, (_, i) => startHour + i),
  );
  async function load() {
    if (loading || loaded) return;
    loading = true;
    failure = "";
    try {
      const all: Meeting[] = [];
      for (const file of files) {
        const r = await fetch(file, { signal: controller.signal });
        if (!r.ok) throw new Error("Schedule unavailable. Try again.");
        all.push(...((await r.json()) as Meeting[]));
      }
      meetings = [
        ...new Map(
          all
            .filter(
              (m) =>
                m.starts_at &&
                m.ends_at &&
                !Number.isNaN(Date.parse(m.starts_at.replace(" ", "T"))) &&
                !Number.isNaN(Date.parse(m.ends_at.replace(" ", "T"))),
            )
            .map((m) => [m.meeting_id, m]),
        ).values(),
      ].sort((a, b) => a.starts_at.localeCompare(b.starts_at));
      const observed = observedAt.slice(0, 10),
        first =
          meetings.find((m) => localTime(m.starts_at).date >= observed) ||
          meetings[0];
      week = monday(first ? localTime(first.starts_at).date : observed);
      loaded = true;
    } catch (e) {
      if (!controller.signal.aborted) failure = (e as Error).message;
    } finally {
      loading = false;
    }
  }
  onMount(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          load();
          observer.disconnect();
        }
      },
      { rootMargin: "300px" },
    );
    observer.observe(host);
    return () => {
      observer.disconnect();
      controller.abort();
    };
  });
  async function download() {
    try {
      const { createEvents } = await import("ics");
      const date = (
        value: string,
      ): [number, number, number, number, number] => {
        const d = new Date(value.replace(" ", "T"));
        return [
          d.getUTCFullYear(),
          d.getUTCMonth() + 1,
          d.getUTCDate(),
          d.getUTCHours(),
          d.getUTCMinutes(),
        ];
      };
      const { value, error } = createEvents(
        filtered.map((m) => ({
          uid: m.meeting_id + "@uwcourses.com",
          title: [m.course_id, sectionName(m.name)].filter(Boolean).join(" · "),
          start: date(m.starts_at),
          end: date(m.ends_at),
          startInputType: "utc" as const,
          endInputType: "utc" as const,
          location: [m.building, m.room].filter(Boolean).join(" "),
          description: (m.instructor_names || []).join(", "),
        })),
      );
      if (error || !value) throw new Error("Unable to export schedule.");
      const url = URL.createObjectURL(
        new Blob([value], { type: "text/calendar;charset=utf-8" }),
      );
      const link = document.createElement("a");
      link.href = url;
      link.download = "course-schedule.ics";
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) {
      failure = (e as Error).message;
    }
  }
</script>

<div bind:this={host} class="course-calendar">
  {#if failure}<p role="alert">{failure}</p>
    {#if !loaded}<button onclick={load}>Retry schedule</button>{/if}{/if}
  {#if !loaded}<p class="empty">
      {loading ? "Loading schedule…" : "Schedule loads here as you scroll."}
    </p>
    <noscript
      ><p>
        Download meeting source records below to view the schedule without
        JavaScript.
      </p></noscript
    >
  {:else if !meetings.length}<p class="empty">
      No scheduled meetings recorded.
    </p>
  {:else}
    <div class="calendar-tools">
      <div class="row">
        <button
          aria-label="Previous week"
          onclick={() => (week = addDays(week, -7))}
          ><ChevronLeft size={15} /></button
        ><span class="mono week-label"
          >{dayLabel(week)} – {dayLabel(addDays(week, 6))}, {week.slice(
            0,
            4,
          )}</span
        ><button
          aria-label="Next week"
          onclick={() => (week = addDays(week, 7))}
          ><ChevronRight size={15} /></button
        >
      </div>
      <div class="row">
        <select aria-label="Calendar section" bind:value={section}
          ><option value="">All sections</option
          >{#each [...new Set(meetings.map( (m) => sectionName(m.name), ))].sort() as name}<option
              >{name}</option
            >{/each}</select
        ><button class="export" onclick={download}
          ><Download size={13} /> Export</button
        >
      </div>
    </div>
    <div
      class="week-grid"
      style={`--days:${shownDays.length};--hours:${hours.length}`}
    >
      <div class="day-header time-zone">CT</div>
      {#each shownDays as day, i}<div class="day-header">
          <span>{["mon", "tue", "wed", "thu", "fri", "sat", "sun"][i]}</span
          ><strong>{Number(day.slice(-2))}</strong>
        </div>{/each}
      <div class="hour-axis">
        {#each hours as hour}<span>{timeLabel(hour * 60)}</span>{/each}
      </div>
      {#each shownDays as day}<div class="day-column">
          {#each placeMeetings(filtered, day) as event}<button
              class="meeting"
              style={`top:${((event.start - startHour * 60) / 60) * 48}px;height:${Math.max(25, ((event.end - event.start) / 60) * 48)}px;left:calc(${(event.lane / event.lanes) * 100}% + 2px);width:calc(${100 / event.lanes}% - 4px)`}
              onclick={() => (selected = event.meeting)}
              title={`${sectionName(event.meeting.name)} · ${timeLabel(event.start)}–${timeLabel(event.end)} · ${event.meeting.building || ""} ${event.meeting.room || ""}`}
              ><strong>{sectionName(event.meeting.name)}</strong><span
                >{timeLabel(event.start)}</span
              ><span>{event.meeting.room} {event.meeting.building}</span
              ></button
            >{/each}
        </div>{/each}
    </div>
    <div class="agenda">
      {#each shownDays as day}{@const entries = placeMeetings(
          filtered,
          day,
        )}{#if entries.length}<h3>{dayLabel(day)}</h3>
          {#each entries as event}<button
              onclick={() => (selected = event.meeting)}
              ><span class="mono">{timeLabel(event.start)}</span><strong
                >{sectionName(event.meeting.name)}</strong
              ><span class="muted"
                >{event.meeting.building} {event.meeting.room}</span
              ></button
            >{/each}{/if}{/each}
    </div>
    {#if !visible.length}<p class="empty">
        No meetings recorded this week.
      </p>{/if}
    {#if selected}<div
        class="meeting-detail"
        role="region"
        aria-label="Meeting details"
      >
        <div class="row between">
          <strong>{selected.name}</strong><button
            aria-label="Close meeting details"
            onclick={() => (selected = null)}><X size={14} /></button
          >
        </div>
        <p>
          {dayLabel(localTime(selected.starts_at).date)} · {timeLabel(
            localTime(selected.starts_at).minute,
          )}–{timeLabel(localTime(selected.ends_at).minute)}
        </p>
        <p>
          <MapPin size={13} />{[selected.building, selected.room]
            .filter(Boolean)
            .join(" ") || "Location unavailable"}
        </p>
        <p>
          <Users size={13} />{selected.instructor_names?.join(", ") ||
            "Instructor not recorded"}
        </p>
      </div>{/if}
    <p class="calendar-note">
      America/Chicago · Select a meeting for details. Export includes all
      recorded dates for the selected sections.
    </p>
  {/if}
</div>

<style>
  .calendar-tools {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 18px;
  }
  .calendar-tools .row {
    gap: 6px;
  }
  button {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px;
    border: 0;
    background: transparent;
  }
  .export,
  select {
    font: 11px var(--font-mono);
    padding: 6px 8px;
  }
  .week-label {
    font-size: 11px;
    min-width: 160px;
    text-align: center;
  }
  .week-grid {
    display: grid;
    grid-template-columns: 40px repeat(var(--days), minmax(0, 1fr));
    border: 1px solid var(--border);
    border-radius: 4px;
    overflow: hidden;
  }
  .day-header {
    text-align: center;
    padding: 10px 0;
    border-bottom: 1px solid var(--border);
    font: 10px var(--font-mono);
    color: var(--muted);
    display: grid;
    gap: 4px;
  }
  .day-header strong {
    font-size: 15px;
    color: var(--text);
    font-weight: 450;
  }
  .time-zone {
    place-content: center;
  }
  .hour-axis {
    display: grid;
    grid-template-rows: repeat(var(--hours), 48px);
    font: 9px var(--font-mono);
    color: var(--muted);
  }
  .hour-axis span {
    padding: 3px;
  }
  .day-column {
    position: relative;
    height: calc(var(--hours) * 48px);
    border-left: 1px solid var(--border);
    background: repeating-linear-gradient(
      to bottom,
      transparent 0,
      transparent 47px,
      var(--border) 47px,
      var(--border) 48px
    );
  }
  .meeting {
    position: absolute;
    display: flex;
    flex-direction: column;
    align-items: start;
    gap: 0;
    overflow: hidden;
    border-left: 2px solid var(--accent);
    border-radius: 3px;
    background: var(--accent-soft);
    padding: 3px 5px;
    text-align: left;
    font: 11px/1.4 var(--font-sans);
    color: var(--text);
  }
  .meeting strong {
    font-weight: 550;
  }
  .meeting span {
    font-size: 11px;
  }
  .meeting:hover {
    background: color-mix(in srgb, var(--accent) 20%, var(--bg));
  }
  .calendar-note {
    font: 10px/1.5 var(--font-mono);
    color: var(--muted);
    margin: 12px 0 20px;
  }
  .meeting-detail {
    border: 1px solid var(--border);
    padding: 12px;
    margin-top: 12px;
    border-radius: 4px;
    font-size: 12px;
  }
  .meeting-detail p {
    display: flex;
    gap: 8px;
    align-items: center;
    margin-top: 5px;
  }
  .agenda {
    display: none;
  }
  .agenda h3 {
    font: 11px var(--font-mono);
    margin: 16px 0 6px;
  }
  .agenda button {
    display: grid;
    grid-template-columns: 65px 1fr;
    text-align: left;
    border-top: 1px solid var(--border);
    width: 100%;
    padding: 10px 0;
    font-size: 12px;
  }
  .agenda button > .muted {
    grid-column: 2;
  }
  @media (max-width: 600px) {
    .week-grid {
      display: none;
    }
    .agenda {
      display: block;
    }
    .calendar-tools {
      gap: 8px;
    }
    .calendar-tools > .row {
      justify-content: space-between;
      width: 100%;
    }
  }
</style>
