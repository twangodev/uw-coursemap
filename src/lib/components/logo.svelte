<script lang="ts">
  import { cn } from "$lib/utils.js";

  const logoPath = "/uw-coursemap-logo.svg";

  interface Props {
    class?: string;
  }

  let { class: className = "" }: Props = $props();
</script>

<div class={cn("flex h-auto w-7 items-center justify-center", className)}>
  <img src={logoPath} alt="Crest" />
</div>
