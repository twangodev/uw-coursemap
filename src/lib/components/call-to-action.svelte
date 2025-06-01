<script>
    import {Button} from "$lib/components/ui/button/index.js";
    import Github from "./icons/github.svelte";
</script>

<div class="mx-auto text-center my-16 max-w-2xl">
    <h2 class="text-balance text-4xl font-bold lg:text-5xl">
        Start Exploring Courses
    </h2>
    <p class="mt-4">
        Start browsing UW's courses and our course maps, or head over to our GitHub to see our roadmap and contribute to the project.
    </p>
    <div class="mt-12 flex flex-wrap justify-center gap-4">
        <Button href="/explorer" class="px-8">Get Started</Button>
        <Button href="https://github.com/twangodev/uw-coursemap" class="py-2" variant="outline">
            <Github />
            GitHub
        </Button>
    </div>
</div>