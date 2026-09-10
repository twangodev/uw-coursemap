<script lang="ts">
  import map from "$lib/assets/campus-map.svg";
  import { campusHeat, type CampusDay } from "$lib/campus";
  let {
    day = null,
    now = null,
  }: { day?: CampusDay | null; now?: number | null } = $props();
  const id = $props.id();
  let heat = $derived(now !== null ? campusHeat(day, now) : []);
</script>

<div class="campus-map" aria-hidden="true">
  <svg viewBox="0 0 900 505" preserveAspectRatio="xMidYMid slice">
    <defs>
      <radialGradient id={`${id}-heat`}>
        <stop offset="0" stop-color="#ff925c" stop-opacity=".85" />
        <stop offset=".28" stop-color="#e64b38" stop-opacity=".65" />
        <stop offset=".6" stop-color="#c4292b" stop-opacity=".25" />
        <stop offset="1" stop-color="#c4292b" stop-opacity="0" />
      </radialGradient>
    </defs>
    <image class="base-map" href={map} width="900" height="505" />
    {#each heat as building (building.name)}
      <circle
        class="building-heat"
        cx={building.x}
        cy={building.y}
        r={10 + Math.sqrt(building.count) * 4}
        fill={`url(#${id}-heat)`}
        data-building={building.name}
        data-meetings={building.count}
      />
      <circle
        class="building-center"
        cx={building.x}
        cy={building.y}
        r={1.5}
        fill="#e76a50"
      />
    {/each}
  </svg>
</div>

<style>
  .campus-map {
    position: absolute;
    inset: 0;
    z-index: -1;
    pointer-events: none;
    mask-image: linear-gradient(transparent, #000 20%, #000 70%, transparent);
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
    opacity: 0.75;
  }
  @media (prefers-reduced-motion: no-preference) {
    .building-heat {
      transition:
        r 800ms ease,
        cx 800ms ease,
        cy 800ms ease;
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
