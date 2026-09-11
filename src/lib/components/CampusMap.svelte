<script lang="ts">
  import { X } from "@lucide/svelte";
  import AnimatedNumber from "./AnimatedNumber.svelte";
  import { courseUrl } from "$lib/format";
  import { madisonZone } from "$lib/campus";
  import { buildingOutlines } from "$lib/campus-buildings";
  import map from "$lib/assets/campus-map.svg";
  import { campusHeat, campusIntensity, type CampusDay } from "$lib/campus";
  let {
    maxConcurrentClasses,
    day = null,
    now = null,
  }: {
    maxConcurrentClasses: number;
    day?: CampusDay | null;
    now?: number | null;
  } = $props();
  let heat = $derived(
    now !== null ? buildingOutlines(campusHeat(day, now, true)) : [],
  );
  let selected = $state<string | null>(null);
  let pinned = $state(false);
  const tooltipId = $props.id();
  let cursor = $state<{ x: number; y: number } | null>(null);
  let viewportWidth = $state(0);
  let viewportHeight = $state(0);
  let panelWidth = $state(350);
  let panelHeight = $state(0);
  const gutter = 12;
  const offset = 16;
  let floating = $derived(cursor !== null && viewportWidth > 700);
  let panelX = $derived(
    cursor
      ? Math.max(
          gutter,
          Math.min(
            cursor.x + offset + panelWidth > viewportWidth - gutter
              ? cursor.x - panelWidth - offset
              : cursor.x + offset,
            viewportWidth - panelWidth - gutter,
          ),
        )
      : 0,
  );
  let panelY = $derived(
    cursor
      ? Math.max(
          gutter,
          Math.min(
            cursor.y + offset,
            viewportHeight - panelHeight - gutter - 1,
          ),
        )
      : 0,
  );
  function followPointer(event: PointerEvent, id: string) {
    if (
      !pinned &&
      event.pointerType === "mouse" &&
      matchMedia("(hover: hover) and (min-width: 701px)").matches
    ) {
      selected = id;
      cursor = { x: event.clientX, y: event.clientY };
    }
  }
  function selectBuilding(id: string) {
    pinned = true;
    selected = id;
  }
  function dismiss() {
    selected = null;
    pinned = false;
    cursor = null;
  }
  let building = $derived(heat.find((b) => b.id === selected));
  let sessions = $derived(
    (day?.buildings ?? [])
      .filter((b) => building?.names.includes(b.name))
      .flatMap((b) => b.sessions ?? [])
      .sort((a, b) => a.startsAt - b.startsAt),
  );
  let active = $derived(
    sessions.filter((s) => now !== null && s.startsAt <= now && s.endsAt > now),
  );
  let known = $derived(active.filter((s) => s.enrolled !== null));
  let students = $derived(
    building?.count === 0
      ? 0
      : known.length
        ? known.reduce((total, s) => total + s.enrolled!, 0)
        : null,
  );
  let rooms = $derived(new Set(active.map((s) => s.room).filter(Boolean)).size);
  const time = (at: number) =>
    new Intl.DateTimeFormat("en-US", {
      timeZone: madisonZone,
      hour: "numeric",
      minute: "2-digit",
    }).format(at);
</script>

<svelte:window
  bind:innerWidth={viewportWidth}
  bind:innerHeight={viewportHeight}
  onkeydown={(event) => {
    if (event.key === "Escape") dismiss();
  }}
  onclick={(event) => {
    if (
      event.target instanceof Element &&
      !event.target.closest(".building-panel, .building-heat")
    )
      dismiss();
  }}
/>
<div class="campus-map">
  <div class="map-art">
    <svg viewBox="0 0 900 505" preserveAspectRatio="xMidYMid slice">
      <image class="base-map" href={map} width="900" height="505" />
      {#each heat as building (building.id)}
        <path
          class="building-heat"
          d={building.path}
          fill="var(--accent)"
          fill-opacity={building.count
            ? 0.08 + campusIntensity(building.count, maxConcurrentClasses) * 0.3
            : 0}
          stroke="var(--accent)"
          stroke-opacity={building.count
            ? 0.45 +
              campusIntensity(building.count, maxConcurrentClasses) * 0.55
            : 0.14}
          stroke-width="1.25"
          stroke-linejoin="round"
          vector-effect="non-scaling-stroke"
          role="button"
          tabindex="0"
          aria-label={`${building.name}: ${building.count} classes in session`}
          aria-expanded={pinned && selected === building.id}
          aria-describedby={!pinned && selected === building.id
            ? tooltipId
            : undefined}
          onpointerenter={(event) => followPointer(event, building.id)}
          onpointermove={(event) => {
            if (selected === building.id) followPointer(event, building.id);
          }}
          onpointerleave={() => {
            if (!pinned) dismiss();
          }}
          onblur={() => {
            if (!pinned) dismiss();
          }}
          onfocus={(event) => {
            if (!pinned && event.currentTarget.matches(":focus-visible")) {
              const rect = event.currentTarget.getBoundingClientRect();
              selected = building.id;
              cursor = { x: rect.right, y: rect.top };
            }
          }}
          onclick={() => selectBuilding(building.id)}
          onkeydown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              selectBuilding(building.id);
            }
          }}
          data-building={building.name}
          data-meetings={building.count}
        />
      {/each}
    </svg>
  </div>
  {#if building}
    <section
      class="building-panel"
      class:floating
      class:building-tooltip={!pinned}
      id={!pinned ? tooltipId : undefined}
      role={pinned ? "region" : "tooltip"}
      bind:offsetWidth={panelWidth}
      bind:offsetHeight={panelHeight}
      style:left={floating ? `${panelX}px` : undefined}
      style:top={floating ? `${panelY}px` : undefined}
      aria-label={`${building.name} details`}
    >
      <header>
        <div>
          <span class="eyebrow">In session now</span>
          <h2>{building.name}</h2>
        </div>
        {#if pinned}<button
            class="close"
            aria-label="Close building details"
            onclick={dismiss}><X size={17} /></button
          >{/if}
      </header>
      <dl>
        <div>
          <dt>Classes now</dt>
          <dd><AnimatedNumber value={building.count} /></dd>
        </div>
        <div>
          <dt>Recorded enrollment</dt>
          <dd><AnimatedNumber value={students} /></dd>
        </div>
        {#if pinned}<div>
            <dt>Rooms in use</dt>
            <dd><AnimatedNumber value={sessions.length ? rooms : null} /></dd>
          </div>
          <div>
            <dt>Meetings today</dt>
            <dd><AnimatedNumber value={sessions.length || null} /></dd>
          </div>{/if}
      </dl>
      {#if !pinned}
        <div class="tooltip-classes">
          {#each active.slice(0, 3) as session}
            <p>
              {session.courses
                .map((course) => course.code)
                .join(" / ")}{session.room ? ` · Room ${session.room}` : ""}
            </p>
          {/each}
          {#if active.length > 3}<p>+{active.length - 3} more classes</p>{/if}
        </div>
        <p class="note">Scheduled enrollment, not live attendance.</p>
        <p class="tooltip-hint">Click for class details</p>
      {:else}
        <div class="classes">
          {#each active as session}
            <article>
              <div class="class-codes">
                {#each session.courses as course, i}{#if i}<span>
                      /
                    </span>{/if}<a href={courseUrl(course.code)}
                    >{course.code}</a
                  >{/each}
              </div>
              <p>
                {[
                  session.courses[0]?.section ?? "Class",
                  session.room ? `Room ${session.room}` : null,
                ]
                  .filter(Boolean)
                  .join(" · ")}
              </p>
              <p>
                {time(session.startsAt)}–{time(
                  session.endsAt,
                )}{session.enrolled !== null
                  ? ` · ${session.enrolled} enrolled`
                  : ""}
              </p>
              {#if session.instructors.length}<p class="instructors">
                  {session.instructors.join(", ")}
                </p>{/if}
            </article>
          {:else}<p class="empty">
              {sessions.length
                ? "No classes in session right now."
                : "Class details are unavailable in this schedule snapshot."}
            </p>{/each}
        </div>
        <p class="note">
          Published schedule and enrollment, not live attendance.{#if known.length < active.length}{" "}
            Enrollment is missing for {active.length - known.length} active {active.length -
              known.length ===
            1
              ? "class"
              : "classes"}.{/if}
        </p>
      {/if}
    </section>
  {/if}
</div>

<style>
  .campus-map {
    position: absolute;
    inset: 0;

    pointer-events: none;
  }
  /* Feather the map without fading the interactive details panel. */
  .map-art {
    position: absolute;
    inset: 0;
    mask-image:
      linear-gradient(
        to right,
        transparent,
        #0004 4%,
        #000b 9%,
        #000 16%,
        #000 84%,
        #000b 91%,
        #0004 96%,
        transparent
      ),
      linear-gradient(
        to bottom,
        transparent,
        #0004 9%,
        #000b 17%,
        #000 26%,
        #000 66%,
        #000b 78%,
        #0004 90%,
        transparent
      );
    mask-composite: intersect;
  }
  svg {
    display: block;
    width: 100%;
    height: 100%;
  }
  .base-map {
    opacity: 0.35;
  }
  :global(.dark) .base-map {
    filter: invert(1);
    opacity: 0.24;
  }
  .building-heat {
    pointer-events: auto;
    cursor: pointer;
    opacity: 0.75;
  }

  .building-heat:hover,
  .building-heat:focus-visible {
    stroke-opacity: 1;
    stroke-width: 2;
    fill-opacity: 0.4;
    outline: none;
  }
  .building-panel {
    position: absolute;
    z-index: 4;
    top: 68px;
    right: 20px;
    width: min(350px, calc(100% - 32px));
    pointer-events: auto;
    padding: 20px;
    border: 1px solid var(--border);
    border-radius: 10px;
    background: var(--bg);
    box-shadow: 0 16px 48px #0003;
  }
  .building-panel.floating {
    position: fixed;
    right: auto;
    width: min(350px, calc(100vw - 24px));
    max-height: calc(100dvh - 24px);
    overflow-y: auto;
  }
  .building-panel.building-tooltip {
    width: min(280px, calc(100vw - 24px));
    padding: 14px 16px;
    pointer-events: none;
  }
  .building-tooltip h2 {
    font-size: 17px;
  }
  .building-tooltip dl {
    margin: 14px 0;
    gap: 12px;
  }
  .building-tooltip dd {
    font-size: 21px;
  }
  .tooltip-classes {
    font-size: 12px;
    line-height: 1.7;
  }
  .tooltip-hint {
    margin-top: 8px;
    font-size: 11px;
    color: var(--muted);
  }
  .building-tooltip .note {
    margin-top: 10px;
  }
  header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
  }
  .eyebrow {
    font-size: 10px;
    color: var(--muted);
  }
  h2 {
    font-size: 21px;
    font-weight: 500;
    letter-spacing: -0.035em;
    margin-top: 4px;
  }
  .close {
    display: grid;
    place-items: center;
    border: 0;
    background: transparent;
    color: var(--muted);
    width: 28px;
    height: 28px;
    cursor: pointer;
  }
  dl {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
    margin: 22px 0;
  }
  dt {
    color: var(--muted);
    font-size: 11px;
  }
  dd {
    font-size: 25px;
    letter-spacing: -0.04em;
    margin: 4px 0 0;
  }
  .classes {
    max-height: 210px;
    overflow: auto;
    overscroll-behavior: contain;
  }
  article {
    padding: 12px 0;
    border-top: 1px solid var(--border);
  }
  .class-codes {
    overflow-wrap: anywhere;
    font-size: 13px;
  }
  .class-codes a {
    color: var(--text);
    text-underline-offset: 3px;
  }
  article p {
    margin: 4px 0 0;
    color: var(--muted);
    font-size: 11px;
    line-height: 1.5;
  }
  .instructors {
    text-wrap: pretty;
  }
  .empty,
  .note {
    color: var(--muted);
    font-size: 11px;
    line-height: 1.5;
  }
  .note {
    margin-top: 16px;
  }
  @media (max-width: 700px) {
    .building-panel {
      top: 100px;
      right: 16px;
    }
    .classes {
      max-height: 170px;
    }
  }
  @media (prefers-reduced-motion: no-preference) {
    .building-heat {
      pointer-events: auto;
      cursor: pointer;
      transition:
        fill-opacity 800ms ease,
        stroke-opacity 800ms ease;
      animation: heat-in 600ms ease both;
    }
    @keyframes heat-in {
      from {
        opacity: 0;
      }
      to {
        opacity: 0.75;
      }
    }
  }
</style>
