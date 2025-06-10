<script lang="ts">
  interface Props {
    hex: string;
    onclick: () => void;
    label?: string;
    hiddenSubject: string | null;
  }

  let { hex, onclick, label = "", hiddenSubject }: Props = $props();

  let enabled = $derived(label != hiddenSubject);
</script>

<div
  class="my-1 flex flex-row items-center space-x-2 {enabled
    ? 'opacity-100'
    : 'opacity-50'}"
>
  <button
    class="h-4 w-4 cursor-pointer rounded-full"
    aria-label="Show/Hide {label}"
    style="background-color: {hex}"
    {onclick}
  ></button>
  <span class="text-sm select-none">{label}</span>
</div>
