<script lang="ts">
    import {LucideMail} from "lucide-svelte";
    import {Avatar, AvatarFallback} from "$lib/components/ui/avatar/index.js";
    import {onMount} from "svelte";
    import {PUBLIC_API_URL} from "$env/static/public";
    import type {Instructor} from "$lib/types/instructor.ts";

    function getRatingColorClass(rating: number | null) {
        if (rating === null || rating < 1 || rating > 5) {
            return "bg-gray-200 text-gray-800 dark:bg-gray-800 dark:text-gray-200";
        } else if (rating >= 1 && rating < 2) {
            return "bg-red-200 text-red-800 dark:bg-red-800 dark:text-red-200";
        } else if (rating >= 2 && rating < 3) {
            return "bg-orange-200 text-orange-800 dark:bg-orange-800 dark:text-orange-200";
        } else if (rating >= 3 && rating < 4) {
            return "bg-yellow-200 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200";
        } else if (rating >= 4 && rating < 5) {
            return "bg-green-200 text-green-800 dark:bg-green-800 dark:text-green-200";
        } else {
            return "bg-blue-200 text-blue-800 dark:bg-blue-800 dark:text-blue-200";
        }
    }

    export let name: string;
    export let email: string;
    export let getRating: boolean = false;
    export let rating: number | null = null;

</script>

<a
        class="flex justify-between items-center p-2 rounded-lg hover:bg-muted transition-colors w-full"
        target="_blank"
        href="/instructors/{name.replaceAll(' ', '_').replaceAll('/', '_')}"
>
    <div class="flex items-center overflow-hidden">
        <Avatar class="flex-shrink-0">
            <AvatarFallback>{name[0]}</AvatarFallback>
        </Avatar>
        <div class="ml-4 flex-1 min-w-0">
            <h4 class="text-sm font-semibold truncate">{name}</h4>
            <div class="flex items-center py-1">
                <LucideMail class="mr-2 h-4 w-4 opacity-70 flex-shrink-0" />
                <span class="text-muted-foreground text-xs underline-offset-2 truncate">{email}</span>
            </div>
        </div>
    </div>
    {#if getRating}
        <div class="min-w-14 py-4 h-full text-xl font-bold flex items-center justify-center rounded-lg {getRatingColorClass(rating)}">
            { rating?.toFixed(1) || "?"}
        </div>
    {/if}
</a>

