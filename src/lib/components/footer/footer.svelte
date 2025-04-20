<script lang="ts">
    import FooterLink from "$lib/components/footer/footer-link.svelte";
    import { page } from "$app/stores";
    import type { Contributor } from "$lib/github";

    const contributors: Contributor[] = $derived($page.data.contributors); 
</script>

<footer class="flex bg-background border-t border-border/40 py-6 dark:border-border md:px-8 md:py-0">
    <div class="container flex flex-col items-center justify-between gap-4 md:h-24 md:flex-row">
        <p class="text-balance text-center text-sm leading-loose text-muted-foreground md:text-left">
            Built by{" "}
            {#each contributors as contributor, i}
                <FooterLink href={contributor.url}>{contributor.name}</FooterLink>
                {#if i < contributors.length - 2},{" "}
                {:else if i < contributors.length - 1},{" "}and{" "}
                {/if}
            {/each}
            . The source code is available on{" "}
            <FooterLink href="https://github.com/twangodev/uw-coursemap">GitHub</FooterLink>.
        </p>
        <p class="text-balance text-center text-sm leading-loose text-muted-foreground md:text-right">
            &copy {new Date().getFullYear()} UW Course Map. Made with 🧀 in Madison.
        </p>
    </div>
</footer>
