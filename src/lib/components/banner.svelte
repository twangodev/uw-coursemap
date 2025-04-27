<script lang="ts">
    import {bannerContents} from "$lib/config/banner.ts";
</script>

<p
        class="bg-secondary text-secondary-foreground py-1.5 text-center text-sm font-medium"
>
    {bannerContents.announcement} -
    <a
            href="{bannerContents.linkHref}"
            target="_blank"
            class="inline-flex items-center font-semibold underline-offset-2 hover:underline"
    >
        {bannerContents.linkText}
        <ArrowUpRight class="ml-0.5 h-3 w-3" />
    </a>
</p>
