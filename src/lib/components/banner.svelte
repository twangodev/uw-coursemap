<script lang="ts">
  import ArrowUpRight from "@lucide/svelte/icons/arrow-up-right";
  import { bannerContents } from "$lib/config/banner.ts";
  import { m } from "$lib/paraglide/messages";
</script>

<p
  class="bg-secondary text-secondary-foreground py-1.5 text-center text-sm font-medium"
>
  {m["banner.announcement"]()} -
  <a
    href={bannerContents.linkHref}
    target="_blank"
    class="inline-flex items-center font-semibold underline-offset-2 hover:underline"
  >
    {m["banner.linkText"]()}
    <ArrowUpRight class="ml-0.5 h-3 w-3" />
  </a>
</p>
