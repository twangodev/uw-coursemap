<script lang="ts">
  import FooterLink from "$lib/components/footer/footer-link.svelte";
  import { VERSION_INFO } from "$lib/generated/version";
</script>

<footer
  class="bg-background border-border/40 dark:border-border flex border-t py-6 md:px-8 md:py-0"
>
  <div
    class="container flex flex-col items-center justify-between gap-4 md:h-24 md:flex-row"
  >
    <div
      class="flex flex-col gap-1 text-muted-foreground text-center text-sm leading-loose text-balance md:text-left "
    >
      <p>
        Made by
        <FooterLink href="https://twango.dev">James Ding</FooterLink>
        and other
        <FooterLink href="https://docs.uwcourses.com/team">contributors</FooterLink>
      </p>
      <p class="text-xs">
        Last synced 4 days ago • {VERSION_INFO.version}
      </p>
    </div>
    <div
      class="flex flex-col gap-1 text-muted-foreground text-center text-base leading-loose text-balance md:text-right "
    >
      <div class="flex items-center justify-center gap-2 sm:justify-end">
        <span class="relative flex">
          <img src="https://kener.twango.dev/badge/uw-coursemap/dot?animate=ping" alt="Service Status" />
        </span>
        <FooterLink href="https://kener.twango.dev/?group=uw-coursemap">View Service Status</FooterLink>
      </div>
    </div>
  </div>
</footer>
