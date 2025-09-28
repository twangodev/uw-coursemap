<script lang="ts">
  import Cytoscape from "$lib/components/cytoscape/cytoscape.svelte";
  import { page } from "$app/state";
  import { env } from "$env/dynamic/public";
  import { onMount } from "svelte";
  import { toast } from "svelte-sonner";
  import { m } from "$lib/paraglide/messages";

  let subject = $derived(page.params.subject?.toUpperCase() ?? '');

  let { data } = $props();

  let elementDefinitions = $derived(data.elementDefinitions);
  let styleEntries = $derived(data.styleEntries);

  onMount(() => {
    toast.message(m["cytoscape.toast.showingCourses"]({ subject }), {
      duration: 5000,
      cancel: {
        label: m["cytoscape.toast.hide"](),
        onClick: () => {
          toast.dismiss();
        },
      },
    });
  });
</script>

{#key [subject]}
  <Cytoscape {elementDefinitions} {styleEntries} />
{/key}
