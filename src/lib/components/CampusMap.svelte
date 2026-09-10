<script lang="ts">
  import { buildingOutlines } from "$lib/campus-buildings";
  import map from "$lib/assets/campus-map.svg";
  import { campusHeat, type CampusDay } from "$lib/campus";
  let {
    day = null,
    now = null,
  }: { day?: CampusDay | null; now?: number | null } = $props();
  let heat = $derived(
    now !== null ? buildingOutlines(campusHeat(day, now)) : [],
  );
</script>

<div class="campus-map" aria-hidden="true">
  <svg viewBox="0 0 900 505" preserveAspectRatio="xMidYMid slice">
    <image class="base-map" href={map} width="900" height="505" />
    {#each heat as building (building.id)}
      <path
        class="building-heat"
        d={building.path}
        fill="var(--accent)"
        fill-opacity={0.08 + Math.min(1, building.count / 25) * 0.3}
        stroke="var(--accent)"
        stroke-opacity={0.45 + Math.min(1, building.count / 25) * 0.55}
        stroke-width="1.25"
        stroke-linejoin="round"
        vector-effect="non-scaling-stroke"
        data-building={building.name}
        data-meetings={building.count}
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
