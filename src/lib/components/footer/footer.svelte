<script lang="ts">
  import FooterLink from "$lib/components/footer/footer-link.svelte";
  import { VERSION_INFO } from "$lib/generated/version";
  import { m } from "$lib/paraglide/messages";

  const { tag, short } = VERSION_INFO;
  
  interface Props {
    lastSynced: string;
  }
  
  let { lastSynced }: Props = $props();
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
        {@html m["footer.madeBy"]({
          author: `<a href="https://twango.dev" target="_blank" class="font-medium underline underline-offset-4">James Ding</a>`,
          contributors: `<a href="https://docs.uwcourses.com/team" target="_blank" class="font-medium underline underline-offset-4">${m["footer.contributors"]()}</a>`
        })}
      </p>
      <p class="text-xs">
        {m["footer.lastSynced"]({ time: lastSynced })} •
        <FooterLink href="https://github.com/twangodev/uw-coursemap/releases/tag/{tag}">{tag}</FooterLink>
        -
        <FooterLink href="https://github.com/twangodev/uw-coursemap/commit/{short}">{short}</FooterLink>
      </p>
    </div>
    <div
      class="flex flex-col gap-1 text-muted-foreground text-center text-xs leading-loose text-balance md:grid-cols-2 md:text-base md:text-right "
    >
      <div class="flex items-center justify-center gap-2 sm:justify-end">
        <span class="relative flex">
          <img src="https://kener.twango.dev/badge/uw-coursemap/dot?animate=ping" alt={m["footer.serviceStatus"]()} />
        </span>
        <FooterLink href="https://kener.twango.dev/?group=uw-coursemap">{m["footer.viewServiceStatus"]()}</FooterLink>
      </div>
    </div>
  </div>
</footer>
