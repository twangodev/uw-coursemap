<script lang="ts">
  import EvidenceBadge from './EvidenceBadge.svelte';
  import type { Badge } from '$lib/badges';
  let { badges, limit = 2 }: { badges: Badge[]; limit?: number } = $props();
</script>
{#if badges.length}<div class="student-badges" aria-label="Student highlights">{#each badges.slice(0, limit) as badge (badge.id)}<EvidenceBadge {badge} />{/each}</div>{/if}
<style>.student-badges { display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0; }</style>
