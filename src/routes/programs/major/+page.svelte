<script lang="ts">
    import { onMount } from "svelte";
    import { PUBLIC_API_URL } from "$env/static/public";

    let majors: string[] = [];

    onMount(async () => {
        const response = await fetch(`${PUBLIC_API_URL}/subjects`);
        const data = await response.json();
        majors = data;
    });
</script>

<main class="py-10">
    <div class="max-w-screen-xl mx-auto px-4">
        <h1 class="text-xl font-semibold mb-6">List of Majors</h1>

        <ul class="space-y-2">
            {#each majors as major}
                <li class="text-sm text-muted-foreground hover:text-foreground transition-colors">
                    <a href={`/explorer/${major}`} class="text-muted-foreground hover:text-foreground transition-colors">
                        {major}
                    </a>
                </li>
            {/each}
        </ul>
    </div>
</main>
