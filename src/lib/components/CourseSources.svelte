<script lang="ts">
  import {
    BookOpen,
    MessageSquare,
    ChartColumn,
    ArrowUpRight,
  } from "@lucide/svelte";
  import Evidence from "./Evidence.svelte";
  import AIDisclaimer from "./AIDisclaimer.svelte";
  import { termName } from "$lib/format";
  let {
    course,
    offerings,
    repository,
  }: { course: any; offerings: any[]; repository: string } = $props();
</script>

<div class="grid grid-cols-3 gap-8 source-grid">
  <section class="min-w-0 source-group" aria-label="Catalog sources">
    <div class="flex items-center gap-2 text-muted text-[12px] publisher">
      <BookOpen size={16} /><span>UW–Madison</span>
    </div>
    <h3 class="text-[20px] font-medium mt-3 mb-2 mx-0">Catalog & offerings</h3>
    <p
      class="text-muted text-[13px] leading-[1.65] mb-6 max-w-[45ch] min-h-[3.3em] description"
    >
      Descriptions, prerequisites, and recorded course offerings.
    </p>
    <Evidence
      title="Catalog observation history"
      files={course.evidence.history || []}
      description="Observations at scan time; dates do not imply when a catalog change took effect."
    />
    <details>
      <summary>Selected offering source records</summary>
      <div class="grid gap-5 text-[13px] offering-list py-4 px-0">
        {#each offerings as offering}
          <article>
            <strong class="font-medium"
              >{offering.course_id} · {termName(offering.term_id)}</strong
            >
            <p class="my-1.5 mx-0">{offering.title}</p>
            <span class="text-muted text-[12px] mt-[5px] date"
              >Recorded {offering.observed_at?.slice(0, 10) ||
                "date unavailable"}</span
            >
          </article>
        {:else}<p
            class="text-muted text-[13px] leading-[1.65] max-w-[45ch] min-h-[3.3em] description my-1.5 mx-0"
          >
            No offering records for the selected term.
          </p>{/each}
      </div>
      <details class="technical-record">
        <summary>Raw records</summary>
        <pre class="max-h-80 overflow-auto">{JSON.stringify(
            offerings,
            null,
            2,
          )}</pre>
      </details>
    </details>
    {#if course.catalog_variants?.length}<details>
        <summary>Cross-listed catalog records</summary>
        <pre class="max-h-80 overflow-auto">{JSON.stringify(
            course.catalog_variants,
            null,
            2,
          )}</pre>
      </details>{/if}
  </section>
  <section class="min-w-0 source-group" aria-label="Review sources">
    <div class="flex items-center gap-2 text-muted text-[12px] publisher">
      <MessageSquare size={16} /><span>Rate My Professors</span>
    </div>
    <h3 class="text-[20px] font-medium mt-3 mb-2 mx-0">Student reviews</h3>
    <p
      class="text-muted text-[13px] leading-[1.65] mb-6 max-w-[45ch] min-h-[3.3em] description"
    >
      Original comments behind the course and instructor summaries.
    </p>
    <Evidence
      title="Read original reviews"
      files={course.evidence.reviews || []}
    />
  </section>
  <section class="min-w-0 source-group" aria-label="Grade sources">
    <div class="flex items-center gap-2 text-muted text-[12px] publisher">
      <ChartColumn size={16} /><span>Madgrades</span>
    </div>
    <h3 class="text-[20px] font-medium mt-3 mb-2 mx-0">Grade history</h3>
    <p
      class="text-muted text-[13px] leading-[1.65] mb-6 max-w-[45ch] min-h-[3.3em] description"
    >
      Recorded grade distributions by term, section, and instructor.
    </p>
    <a
      class="inline-flex items-center gap-1.5 text-[12px] mt-4.5 text-muted grade-link"
      href="#grades">Explore recorded grades <ArrowUpRight size={13} /></a
    >
  </section>
</div>
<div
  class="flex items-center justify-between gap-6 pt-6 mt-9 border-t border-t-border dataset-footer"
>
  <div class="dataset-description">
    <span class="text-[13px]">Dataset & model</span>
    <p class="text-muted text-[12px] mt-[5px]">
      {course.observed_at
        ? `Recorded ${course.observed_at.slice(0, 10)}`
        : "Versioned course records"}
    </p>
  </div>
  <a
    class="inline-flex items-center gap-1.5 text-[12px]"
    href={`https://huggingface.co/datasets/${repository}`}
    >View the dataset on Hugging Face <ArrowUpRight size={14} /></a
  >
</div>
<details class="mt-4.5 technical-sources">
  <summary>Model outputs & technical records</summary>
  <div
    class="flex items-center gap-2 text-[13px] wrap-anywhere model-identity py-4 px-0"
  >
    <span>{course.llm_model || "Model not recorded"}</span><AIDisclaimer
      model={course.llm_model}
      revision={course.llm_model_revision}
    />
  </div>
  <Evidence
    title="LLM outputs across runs"
    files={course.evidence.results || []}
    downloadOnly
  />
  <Evidence
    title="Full model traces"
    files={course.evidence.traces || []}
    downloadOnly
    description="Recorded model configuration, reasoning, and tool conversations."
  />
  <details>
    <summary>Model & dataset provenance</summary>
    <pre class="max-h-80 overflow-auto">{JSON.stringify(
        {
          model: course.llm_model,
          model_revision: course.llm_model_revision,
          task_version: course.llm_task_version,
          output_id: course.llm_output_id,
          requirements_status: course.llm_requirements_status,
          dataset_revision: course.revision,
          observed_at: course.observed_at,
        },
        null,
        2,
      )}</pre>
  </details>
</details>

<style>
  @media (max-width: 800px) {
    .source-grid {
      grid-template-columns: 1fr;
      gap: 32px;
    }
    .dataset-footer {
      align-items: flex-start;
      flex-direction: column;
      gap: 12px;
    }
  }
</style>
