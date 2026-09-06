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
  import { m } from "$lib/paraglide/messages";
  import { isDesktop } from "$lib/mediaStore.ts";

  let helpDialogOpen = $state(false);

  // Import mode to determine current theme
  import { mode } from "mode-watcher";

  const colorGuide = [
    {
      lightColor: "#007F44",
      darkColor: "#4CC38A",
      label: m["cytoscape.help.courseColors.completed"](),
      description: m["cytoscape.help.courseColors.completedDesc"]()
    },
    {
      lightColor: "#B38600",
      darkColor: "#FFD700",
      label: m["cytoscape.help.courseColors.available"](),
      description: m["cytoscape.help.courseColors.availableDesc"]()
    },
    {
      lightColor: "currentColor",
      darkColor: "currentColor",
      label: m["cytoscape.help.courseColors.locked"](),
      description: m["cytoscape.help.courseColors.lockedDesc"]()
    }
  ];
</script>

<div class="absolute top-4 right-4">
  <IconTootipWrapper tooltip={m["cytoscape.controls.help"]()} onclick={() => (helpDialogOpen = true)}>
    <CircleHelp class="h-5 w-5" />
  </IconTootipWrapper>
</div>

<Dialog.Root bind:open={helpDialogOpen}>
  <Dialog.Content class="sm:max-w-4xl lg:max-w-6xl max-h-[90vh] overflow-y-auto">
    <Dialog.Header>
      <Dialog.Title>{m["cytoscape.help.title"]()}</Dialog.Title>
      <Dialog.Description>
        {m["cytoscape.help.description"]()}
      </Dialog.Description>
    </Dialog.Header>

    <div class="grid gap-6 lg:grid-cols-3 md:grid-cols-2">
      <!-- Getting Started -->
      <div class="space-y-3">
        <div class="flex items-center gap-2 mb-3">
          <Sparkles class="h-4 w-4 text-primary" />
          <h3 class="font-semibold">{m["cytoscape.help.quickStart.title"]()}</h3>
        </div>
        <ol class="space-y-3 text-sm">
          <li class="flex gap-3">
            <span class="text-muted-foreground font-mono text-xs mt-0.5">1.</span>
            <div>
              <p class="font-medium">{m["cytoscape.help.quickStart.findCourses"]()}</p>
              <p class="text-muted-foreground text-xs mt-0.5">{m["cytoscape.help.quickStart.findCoursesDesc"]()}</p>
            </div>
          </li>
          <li class="flex gap-3">
            <span class="text-muted-foreground font-mono text-xs mt-0.5">2.</span>
            <div>
              <p class="font-medium">{m["cytoscape.help.quickStart.viewPrerequisites"]()}</p>
              <p class="text-muted-foreground text-xs mt-0.5">{m["cytoscape.help.quickStart.viewPrerequisitesDesc"]()}</p>
            </div>
          </li>
          <li class="flex gap-3">
            <span class="text-muted-foreground font-mono text-xs mt-0.5">3.</span>
            <div>
              <p class="font-medium">{m["cytoscape.help.quickStart.pinPaths"]()}</p>
              <p class="text-muted-foreground text-xs mt-0.5">{m["cytoscape.help.quickStart.pinPathsDesc"]()}</p>
            </div>
          </li>
        </ol>
      </div>

      <!-- Color Guide -->
      <div class="space-y-3">
        <div class="flex items-center gap-2 mb-3">
          <Palette class="h-4 w-4 text-primary" />
          <h3 class="font-semibold">{m["cytoscape.help.courseColors.title"]()}</h3>
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
          <h3 class="font-semibold">{m["cytoscape.help.navigation.title"]()}</h3>
        </div>
        <div class="space-y-4">
          <div>
            <p class="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">{m["cytoscape.help.navigation.controls"]()}</p>
            <dl class="space-y-1.5 text-sm">
              <div class="flex gap-2">
                <dt class="font-medium min-w-[50px]">{m["cytoscape.help.navigation.pan"]()}</dt>
                <dd class="text-muted-foreground">{m["cytoscape.help.navigation.panDesc"]()}</dd>
              </div>
              <div class="flex gap-2">
                <dt class="font-medium min-w-[50px]">{m["cytoscape.help.navigation.zoom"]()}</dt>
                <dd class="text-muted-foreground">{m["cytoscape.help.navigation.zoomDesc"]()}</dd>
              </div>
              <div class="flex gap-2">
                <dt class="font-medium min-w-[50px]">{m["cytoscape.help.navigation.select"]()}</dt>
                <dd class="text-muted-foreground">{m["cytoscape.help.navigation.selectDesc"]({
                  action: $isDesktop ? m["cytoscape.help.navigation.click"]() : m["cytoscape.help.navigation.tap"]()
                })}</dd>
              </div>
              <div class="flex gap-2">
                <dt class="font-medium min-w-[50px]">{m["cytoscape.help.navigation.pin"]()}</dt>
                <dd class="text-muted-foreground">{m["cytoscape.help.navigation.pinDesc"]()}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>

      <!-- Graph Controls -->
      <div class="space-y-3">
        <div class="flex items-center gap-2 mb-3">
          <Settings2 class="h-4 w-4 text-primary" />
          <h3 class="font-semibold">{m["cytoscape.help.graphControls.title"]()}</h3>
        </div>
        <div class="space-y-3">
          <div class="flex items-start gap-3">
            <div class="h-8 w-8 rounded-md border border-border flex items-center justify-center flex-shrink-0">
              <LucideHash class="h-3.5 w-3.5 text-muted-foreground" />
            </div>
            <div class="text-sm">
              <p class="font-medium">{m["cytoscape.help.graphControls.toggleLabels"]()}</p>
              <p class="text-xs text-muted-foreground mt-0.5">{m["cytoscape.help.graphControls.toggleLabelsDesc"]()}</p>
            </div>
          </div>
          <div class="flex items-start gap-3">
            <div class="h-8 w-8 rounded-md border border-border flex items-center justify-center flex-shrink-0">
              <span class="text-xs">🔒</span>
            </div>
            <div class="text-sm">
              <p class="font-medium">{m["cytoscape.help.graphControls.lockUnlock"]()}</p>
              <p class="text-xs text-muted-foreground mt-0.5">{m["cytoscape.help.graphControls.lockUnlockDesc"]()}</p>
            </div>
          </div>
          <div class="flex items-start gap-3">
            <div class="h-8 w-8 rounded-md border border-border flex items-center justify-center flex-shrink-0">
              <span class="text-xs">⊞</span>
            </div>
            <div class="text-sm">
              <p class="font-medium">{m["cytoscape.help.graphControls.layoutMode"]()}</p>
              <p class="text-xs text-muted-foreground mt-0.5">{m["cytoscape.help.graphControls.layoutModeDesc"]()}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Pro Tips -->
      <div class="space-y-3 lg:col-span-2 md:col-span-1">
        <div class="flex items-center gap-2 mb-3">
          <Info class="h-4 w-4 text-primary" />
          <h3 class="font-semibold">{m["cytoscape.help.proTips.title"]()}</h3>
        </div>
        <div class="grid lg:grid-cols-2 gap-3">
          <div class="space-y-3">
            <div class="flex items-start gap-2">
              <span class="text-muted-foreground mt-0.5">•</span>
              <div class="text-sm">
                <p class="font-medium">{m["cytoscape.help.proTips.uploadTranscript"]()}</p>
                <p class="text-xs text-muted-foreground mt-0.5">{m["cytoscape.help.proTips.uploadTranscriptDesc"]()}</p>
              </div>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-muted-foreground mt-0.5">•</span>
              <div class="text-sm">
                <p class="font-medium">{m["cytoscape.help.proTips.quickSearch"]()}</p>
                <p class="text-xs text-muted-foreground mt-0.5">{m["cytoscape.help.proTips.quickSearchDesc"]()}</p>
              </div>
            </div>
          </div>
          <div class="space-y-3">
            <div class="flex items-start gap-2">
              <span class="text-muted-foreground mt-0.5">•</span>
              <div class="text-sm">
                <p class="font-medium">{m["cytoscape.help.proTips.optimizedPaths"]()}</p>
                <p class="text-xs text-muted-foreground mt-0.5">{m["cytoscape.help.proTips.optimizedPathsDesc"]()}</p>
              </div>
            </div>
            <div class="flex items-start gap-2">
              <span class="text-muted-foreground mt-0.5">•</span>
              <div class="text-sm">
                <p class="font-medium">{m["cytoscape.help.proTips.departmentView"]()}</p>
                <p class="text-xs text-muted-foreground mt-0.5">{m["cytoscape.help.proTips.departmentViewDesc"]()}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <Dialog.Footer>
      <Button onclick={() => (helpDialogOpen = false)}>{m["cytoscape.help.gotIt"]()}</Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>