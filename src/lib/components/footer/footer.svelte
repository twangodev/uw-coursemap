<script>
  import FooterLink from "$lib/components/footer/footer-link.svelte";
  import FooterSource from "./footer-source.svelte";
</script>

<footer
  class="bg-background border-border/40 dark:border-border flex border-t py-6 md:px-8 md:py-0"
>
  <div
    class="container flex flex-col items-center justify-between gap-4 md:h-24 md:flex-row"
  >
    <p
      class="text-muted-foreground text-center text-sm leading-loose text-balance md:text-left"
    >
      <FooterSource />
    </p>
    <p
      class="text-muted-foreground text-center text-sm leading-loose text-balance md:text-right"
    >
      &copy {new Date().getFullYear()} UW Course Map. Made with 🧀 in Madison.
    </p>
  </div>
</footer>
