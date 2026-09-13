<script lang="ts">
  import PopoverSurface from "./PopoverSurface.svelte";
  import Select from "./Select.svelte";
  import { onMount } from "svelte";
  import { Popover } from "bits-ui";
  import { MediaQuery } from "svelte/reactivity";
  import {
    ChevronLeft,
    ChevronRight,
    Download,
    X,
    MapPin,
    Users,
    Clock,
    ArrowUpRight,
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
  let anchor = $state<HTMLElement | null>(null);
  const hourHeight = 72;
  const mobile = new MediaQuery("(max-width: 600px)");
  function openMeeting(meeting: Meeting, target: HTMLElement) {
    anchor = target;
    selected = meeting;
  }
  $effect(() => {
    week;
    section;
    selected = null;
  });
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
    {#if !loaded}<button
        class="inline-flex items-center gap-1.5 p-[5px] border-0 bg-transparent"
        onclick={load}>Retry schedule</button
      >{/if}{/if}
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
    <div class="flex justify-between gap-3 flex-wrap mb-4.5 calendar-tools">
      <div class="gap-1.5 row">
        <button
          class="inline-flex items-center gap-1.5 p-[5px] border-0 bg-transparent"
          aria-label="Previous week"
          onclick={() => (week = addDays(week, -7))}
          ><ChevronLeft size={15} /></button
        ><span class="text-[11px] min-w-40 text-center mono week-label"
          >{dayLabel(week)} – {dayLabel(addDays(week, 6))}, {week.slice(
            0,
            4,
          )}</span
        ><button
          class="inline-flex items-center gap-1.5 p-[5px] border-0 bg-transparent"
          aria-label="Next week"
          onclick={() => (week = addDays(week, 7))}
          ><ChevronRight size={15} /></button
        >
      </div>
      <div class="gap-1.5 row">
        <Select
          label="Calendar section"
          bind:value={section}
          options={[
            { value: "", label: "All sections" },
            ...[...new Set(meetings.map((m) => sectionName(m.name)))]
              .sort()
              .map((name) => ({ value: name, label: name })),
          ]}
        />
        <button
          class="inline-flex items-center gap-1.5 border-0 bg-transparent export py-1.5 px-2"
          onclick={download}><Download size={13} /> Export</button
        >
      </div>
    </div>
    <div
      class="grid grid-cols-[40px_repeat(var(--days),_minmax(0,_1fr))] border border-border rounded-[4px] overflow-hidden week-grid"
      style={`--days:${shownDays.length};--hours:${hours.length};--hour-height:${hourHeight}px`}
    >
      <div
        class="text-center border-b border-b-border text-muted grid gap-1 day-header time-zone py-2.5 px-0"
      >
        CT
      </div>
      {#each shownDays as day, i}<div
          class="text-center border-b border-b-border text-muted grid gap-1 day-header py-2.5 px-0"
        >
          <span>{["mon", "tue", "wed", "thu", "fri", "sat", "sun"][i]}</span
          ><strong class="text-[15px] text-foreground font-[450]"
            >{Number(day.slice(-2))}</strong
          >
        </div>{/each}
      <div class="grid text-muted hour-axis">
        {#each hours as hour}<span class="p-[3px]">{timeLabel(hour * 60)}</span
          >{/each}
      </div>
      {#each shownDays as day}<div
          class="relative h-[calc(var(--hours)_*_var(--hour-height))] border-l border-l-border day-column"
        >
          {#each placeMeetings(filtered, day) as event}<button
              class="flex items-start gap-0 border-0 bg-accent-soft absolute flex-col overflow-hidden rounded-[3px] text-left text-foreground meeting py-1 px-1.5"
              style={`top:${((event.start - startHour * 60) / 60) * hourHeight}px;height:${Math.max(28, ((event.end - event.start) / 60) * hourHeight)}px;left:calc(${(event.lane / event.lanes) * 100}% + 2px);width:calc(${100 / event.lanes}% - 4px)`}
              onclick={(eventClick) =>
                openMeeting(event.meeting, eventClick.currentTarget)}
              aria-haspopup="dialog"
              title={`${sectionName(event.meeting.name)} · ${timeLabel(event.start)}–${timeLabel(event.end)} · ${event.meeting.building || ""} ${event.meeting.room || ""}`}
              ><strong
                class="font-[550] w-full min-h-3.5 leading-[14px] shrink-0 whitespace-nowrap overflow-hidden text-ellipsis"
                >{sectionName(event.meeting.name)}</strong
              >
              {#if event.end - event.start >= 30}<span
                  class="w-full min-h-3.5 leading-[14px] shrink-0 whitespace-nowrap overflow-hidden text-ellipsis text-[11px]"
                  >{timeLabel(event.start)}–{timeLabel(event.end)}</span
                >{/if}
              {#if event.end - event.start >= 45}<span
                  class="w-full min-h-3.5 leading-[14px] shrink-0 whitespace-nowrap overflow-hidden text-ellipsis text-[11px] meeting-location"
                  >{event.meeting.room} {event.meeting.building}</span
                >{/if}
            </button>{/each}
        </div>{/each}
    </div>
    <div class="hidden agenda">
      {#each shownDays as day}{@const entries = placeMeetings(
          filtered,
          day,
        )}{#if entries.length}<h3 class="mt-4 mb-1.5 mx-0">{dayLabel(day)}</h3>
          {#each entries as event}<button
              class="grid items-center gap-1.5 border-0 bg-transparent grid-cols-[65px_1fr] text-left border-t border-t-border w-full text-[12px] py-2.5 px-0"
              onclick={(eventClick) =>
                openMeeting(event.meeting, eventClick.currentTarget)}
              aria-haspopup="dialog"
              ><span class="mono">{timeLabel(event.start)}</span><strong
                >{sectionName(event.meeting.name)}</strong
              ><span class="[grid-column:2] muted"
                >{event.meeting.building} {event.meeting.room}</span
              ></button
            >{/each}{/if}{/each}
    </div>
    {#if !visible.length}<p class="empty">
        No meetings recorded this week.
      </p>{/if}
    <Popover.Root
      open={!!selected}
      onOpenChange={(open) => {
        if (!open) selected = null;
      }}
    >
      <PopoverSurface
        width={360}
        padding="roomy"
        class="max-h-[min(520px,_var(--bits-popover-content-available-height))] overflow-auto meeting-popover"
        customAnchor={anchor}
        side={mobile.current ? "bottom" : "right"}
        align={mobile.current ? "center" : "start"}
        sideOffset={10}
        collisionPadding={12}
        role="dialog"
        aria-label="Meeting details"
        onCloseAutoFocus={(event) => {
          event.preventDefault();
          anchor?.focus();
        }}
      >
        {#if selected}
          <div
            class="flex items-center justify-between gap-4 text-[12px] text-muted meeting-popover-heading"
          >
            <span>{selected.course_id} · {sectionName(selected.name)}</span
            ><Popover.Close
              class="grid place-items-center p-1 border-0 bg-transparent text-muted meeting-close"
              aria-label="Close meeting details"><X size={16} /></Popover.Close
            >
          </div>
          <h3
            class="text-[20px] font-medium leading-[1.35] mt-3 mb-6 wrap-anywhere meeting-title mx-0"
          >
            {sectionName(selected.name)}
          </h3>
          <div
            class="flex items-start gap-3 mt-5 text-[14px] leading-[1.5] meeting-detail-row"
          >
            <Clock size={17} />
            <div class="min-w-0 wrap-anywhere">
              <strong class="font-medium"
                >{dayLabel(localTime(selected.starts_at).date)}</strong
              >
              <p class="mt-[3px] mb-0 text-muted text-[13px] mx-0">
                {timeLabel(localTime(selected.starts_at).minute)}–{timeLabel(
                  localTime(selected.ends_at).minute,
                )} · Central time
              </p>
            </div>
          </div>
          <div
            class="flex items-start gap-3 mt-5 text-[14px] leading-[1.5] meeting-detail-row"
          >
            <MapPin size={17} />
            <div class="min-w-0 wrap-anywhere">
              <strong class="font-medium"
                >{selected.building || "Location unavailable"}</strong
              >{#if selected.room}<p
                  class="mt-[3px] mb-0 text-muted text-[13px] mx-0"
                >
                  Room {selected.room}
                </p>{/if}
              {#if selected.building}<a
                  class="inline-flex items-center gap-1 mt-2 text-[13px]"
                  href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(selected.building + " University of Wisconsin Madison")}`}
                  target="_blank"
                  rel="noreferrer"
                  >Open in Google Maps <ArrowUpRight size={13} /></a
                >{/if}
            </div>
          </div>
          <div
            class="flex items-start gap-3 mt-5 text-[14px] leading-[1.5] meeting-detail-row"
          >
            <Users size={17} />
            <div class="min-w-0 wrap-anywhere">
              {selected.instructor_names?.join(", ") ||
                "Instructor not recorded"}
            </div>
          </div>
        {/if}
      </PopoverSurface>
    </Popover.Root>
  {/if}
</div>

<style>
  .export {
    font: 11px var(--font-sans);
  }
  .day-header {
    font: 10px var(--font-sans);
  }
  .time-zone {
    place-content: center;
  }
  .hour-axis {
    grid-template-rows: repeat(var(--hours), var(--hour-height));
    font: 9px var(--font-sans);
  }
  .day-column {
    background: repeating-linear-gradient(
      to bottom,
      transparent 0,
      transparent calc(var(--hour-height) - 1px),
      var(--border) calc(var(--hour-height) - 1px),
      var(--border) var(--hour-height)
    );
  }
  .meeting {
    border-left: 2px solid var(--accent);
    font: 11px/1.4 var(--font-sans);
  }
  .meeting:hover {
    background: color-mix(in srgb, var(--accent) 20%, var(--bg));
  }
  .meeting-detail-row :global(svg) {
    flex-shrink: 0;
    margin-top: 2px;
    color: var(--muted);
  }
  .agenda h3 {
    font: 11px var(--font-sans);
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
