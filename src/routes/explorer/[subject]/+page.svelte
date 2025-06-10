<script lang="ts">
  import Cytoscape from "$lib/components/cytoscape/cytoscape.svelte";
  import { page } from "$app/state";
  import { env } from "$env/dynamic/public";
  import { onMount } from "svelte";
  import { toast } from "svelte-sonner";

  let subject = $derived(page.params.subject.toUpperCase());

  let { data } = $props();

  let elementDefinitions = $derived(data.elementDefinitions);
  let styleEntries = $derived(data.styleEntries);

  onMount(() => {
    toast.message(`Showing all ${subject} courses`, {
      duration: 5000,
      cancel: {
        label: "Hide",
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
