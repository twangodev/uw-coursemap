<script>
    import {Card, CardContent} from "$lib/components/ui/card/index.ts";
    import {Skeleton} from "$lib/components/ui/skeleton";
</script>

<Card class="w-full max-w-64 overflow-hidden">
    <CardContent class="p-4 pb-0">
        <Skeleton class="h-4 w-3/4 mb-2" />
        <Skeleton class="h-3 w-1/2 mb-2" />
        <Skeleton class="h-3 w-full mb-2" />
        <Skeleton class="h-3 w-full mb-2" />
        <Skeleton class="h-3 w-3/4 mt-2" />
    </CardContent>
</Card>