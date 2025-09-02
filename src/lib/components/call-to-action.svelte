<script>
  import { Button } from "$lib/components/ui/button/index.js";
  import Github from "./icons/github.svelte";
  import { inView } from "$lib/actions/in-view";
</script>

<div use:inView={{ threshold: 0.5 }} class="mx-auto my-16 max-w-2xl text-center">
  <h2 class="text-4xl font-bold text-balance lg:text-5xl opacity-0 animate-scale-in [animation-fill-mode:forwards] [&.in-view]:opacity-100">
    Start Exploring Courses
  </h2>
  <p class="text-muted-foreground mt-4 opacity-0 animate-fade-up [animation-delay:100ms] [animation-fill-mode:forwards] [&.in-view]:opacity-100">
    Start browsing UW's courses and our course maps, or head over to our GitHub
    to see our roadmap and contribute to the project.
  </p>
  <div class="mt-12 flex flex-wrap justify-center gap-4">
    <Button href="/explorer" class="px-8 opacity-0 animate-fade-up [animation-delay:200ms] [animation-fill-mode:forwards] [&.in-view]:opacity-100">Get Started</Button>
    <Button
      href="https://github.com/twangodev/uw-coursemap"
      class="py-2 opacity-0 animate-fade-up [animation-delay:300ms] [animation-fill-mode:forwards] [&.in-view]:opacity-100"
      variant="outline"
    >
      <Github />
      GitHub
    </Button>
  </div>
</div>
