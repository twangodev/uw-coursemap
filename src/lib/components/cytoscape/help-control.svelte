<script lang="ts">
  import { 
    CircleHelp, 
    Info, 
    Palette,
    MousePointer,
    Settings2,
    Sparkles
  } from "@lucide/svelte";
  import IconTootipWrapper from "../icon-toolips/icon-tootip-wrapper.svelte";
  import * as Dialog from "$lib/components/ui/dialog";
  import { Button } from "$lib/components/ui/button";
  import { LucideHash } from "@lucide/svelte";

  interface Props {
    isDesktop: boolean;
  }

  let { isDesktop }: Props = $props();
  let helpDialogOpen = $state(false);

  // Import mode to determine current theme
  import { mode } from "mode-watcher";

  const colorGuide = [
    {
      lightColor: "#007F44",
      darkColor: "#4CC38A",
      label: "Completed",
      description: "Courses you've taken"
    },
    {
      lightColor: "#B38600",
      darkColor: "#FFD700",
      label: "Available",
      description: "Courses with no prerequisites"
    },
    {
      lightColor: "currentColor",
      darkColor: "currentColor",
      label: "Locked",
      description: "Courses with unmet prerequisites"
    }
  ];
</script>

<div class="absolute top-4 right-4">
  <IconTootipWrapper tooltip="Help" onclick={() => (helpDialogOpen = true)}>
    <CircleHelp class="h-5 w-5" />
  </IconTootipWrapper>
</div>

<Dialog.Root bind:open={helpDialogOpen}>
  <Dialog.Content class="sm:max-w-4xl lg:max-w-6xl max-h-[90vh] overflow-y-auto">
    <Dialog.Header>
      <Dialog.Title>Prerequisite Explorer Help</Dialog.Title>
      <Dialog.Description>
        Learn how to navigate and interact with the course dependency graph
      </Dialog.Description>
    </Dialog.Header>

    <div class="grid gap-6 lg:grid-cols-3 md:grid-cols-2">
      <!-- Getting Started -->
      <div class="space-y-3">
        <div class="flex items-center gap-2 mb-3">
          <Sparkles class="h-4 w-4 text-primary" />
          <h3 class="font-semibold">Quick Start</h3>
        </div>
        <ol class="space-y-3 text-sm">
          <li class="flex gap-3">
            <span class="text-muted-foreground font-mono text-xs mt-0.5">1.</span>
            <div>
              <p class="font-medium">Find courses</p>
              <p class="text-muted-foreground text-xs mt-0.5">Search with Ctrl+K or explore visually</p>
            </div>
          </li>
          <li class="flex gap-3">
            <span class="text-muted-foreground font-mono text-xs mt-0.5">2.</span>
            <div>
              <p class="font-medium">View prerequisites</p>
              <p class="text-muted-foreground text-xs mt-0.5">Hover to see dependency chains</p>
            </div>
          </li>
          <li class="flex gap-3">
            <span class="text-muted-foreground font-mono text-xs mt-0.5">3.</span>
            <div>
              <p class="font-medium">Pin paths</p>
              <p class="text-muted-foreground text-xs mt-0.5">Double-tap to keep highlighted</p>
            </div>
          </li>
        </ol>
      </div>

      <!-- Color Guide -->
      <div class="space-y-3">
        <div class="flex items-center gap-2 mb-3">
          <Palette class="h-4 w-4 text-primary" />
          <h3 class="font-semibold">Course Colors</h3>
        </div>
        <div class="space-y-3">
          {#each colorGuide as item}
            <div class="flex items-center gap-3">
              <div 
                class="h-4 w-4 rounded-full border flex-shrink-0" 
                style="background-color: {mode.current === 'dark' ? item.darkColor : item.lightColor}"
              ></div>
              <div class="text-sm">
                <p class="font-medium">{item.label}</p>
                <p class="text-xs text-muted-foreground mt-0.5">{item.description}</p>
              </div>
            </div>
          {/each}
        </div>
      </div>

      <!-- Navigation -->
      <div class="space-y-3">
        <div class="flex items-center gap-2 mb-3">
          <MousePointer class="h-4 w-4 text-primary" />
          <h3 class="font-semibold">Navigation</h3>
        </div>
        <div class="space-y-4">
          <div>
            <p class="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">Controls</p>
            <dl class="space-y-1.5 text-sm">
              <div class="flex gap-2">
                <dt class="font-medium min-w-[50px]">Pan:</dt>
                <dd class="text-muted-foreground">Drag empty space</dd>
              </div>
              <div class="flex gap-2">
                <dt class="font-medium min-w-[50px]">Zoom:</dt>
                <dd class="text-muted-foreground">Scroll or pinch</dd>
              </div>
              <div class="flex gap-2">
                <dt class="font-medium min-w-[50px]">Select:</dt>
                <dd class="text-muted-foreground">{isDesktop ? "Click" : "Tap"} course</dd>
              </div>
              <div class="flex gap-2">
                <dt class="font-medium min-w-[50px]">Pin:</dt>
                <dd class="text-muted-foreground">Double-tap course</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>

      <!-- Graph Controls -->
      <div class="space-y-3">
        <div class="flex items-center gap-2 mb-3">
          <Settings2 class="h-4 w-4 text-primary" />
          <h3 class="font-semibold">Graph Controls</h3>
        </div>
        <div class="space-y-3">
          <div class="flex items-start gap-3">
            <div class="h-8 w-8 rounded-md border border-border flex items-center justify-center flex-shrink-0">
              <LucideHash class="h-3.5 w-3.5 text-muted-foreground" />
            </div>
            <div class="text-sm">
              <p class="font-medium">Toggle Labels</p>
              <p class="text-xs text-muted-foreground mt-0.5">Course codes ↔ titles</p>
            </div>
          </div>
          <div class="flex items-start gap-3">
            <div class="h-8 w-8 rounded-md border border-border flex items-center justify-center flex-shrink-0">
              <span class="text-xs">🔒</span>
            </div>
            <div class="text-sm">
              <p class="font-medium">Lock/Unlock</p>
              <p class="text-xs text-muted-foreground mt-0.5">Drag nodes manually</p>
            </div>
          </div>
          <div class="flex items-start gap-3">
            <div class="h-8 w-8 rounded-md border border-border flex items-center justify-center flex-shrink-0">
              <span class="text-xs">⊞</span>
            </div>
            <div class="text-sm">
              <p class="font-medium">Layout Mode</p>
              <p class="text-xs text-muted-foreground mt-0.5">Groups ↔ layers</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Pro Tips -->
      <div class="space-y-3 lg:col-span-2 md:col-span-1">
        <div class="flex items-center gap-2 mb-3">
          <Info class="h-4 w-4 text-primary" />
          <h3 class="font-semibold">Pro Tips</h3>
        </div>
        <div class="grid lg:grid-cols-2 gap-3">
          <div class="space-y-3">
            <div class="flex items-start gap-2">
              <span class="text-muted-foreground mt-0.5">•</span>
              <div class="text-sm">
                <p class="font-medium">Upload Transcript</p>
                <p class="text-xs text-muted-foreground mt-0.5">See completed courses in green</p>
              </div>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-muted-foreground mt-0.5">•</span>
              <div class="text-sm">
                <p class="font-medium">Quick Search</p>
                <p class="text-xs text-muted-foreground mt-0.5">Ctrl+K finds any course instantly</p>
              </div>
            </div>
          </div>
          <div class="space-y-3">
            <div class="flex items-start gap-2">
              <span class="text-muted-foreground mt-0.5">•</span>
              <div class="text-sm">
                <p class="font-medium">Optimized Paths</p>
                <p class="text-xs text-muted-foreground mt-0.5">Shows simplest prerequisites only</p>
              </div>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-muted-foreground mt-0.5">•</span>
              <div class="text-sm">
                <p class="font-medium">Department View</p>
                <p class="text-xs text-muted-foreground mt-0.5">Group by department in layout</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <Dialog.Footer>
      <Button onclick={() => (helpDialogOpen = false)}>Got it</Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>