<script lang="ts">
  import { page } from "$app/state";
</script>

<div class="hero">
  <p class="eyebrow">{page.status}</p>
  <h1>{page.error?.message || "Something went wrong"}</h1>
  <a href="/search">Explore courses →</a>
</div>
