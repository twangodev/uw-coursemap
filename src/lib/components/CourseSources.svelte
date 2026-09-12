<script lang="ts">
  import { BookOpen, MessageSquare, ChartColumn, ArrowUpRight } from "@lucide/svelte";
  import Evidence from "./Evidence.svelte";
  import AIDisclaimer from "./AIDisclaimer.svelte";
  import { termName } from "$lib/format";
  let { course, offerings, repository }: { course: any; offerings: any[]; repository: string } = $props();
</script>

<div class="source-grid">
  <section class="source-group" aria-label="Catalog sources">
    <div class="publisher"><BookOpen size={16} /><span>UW–Madison</span></div>
    <h3>Catalog & offerings</h3>
    <p class="description">Descriptions, prerequisites, and recorded course offerings.</p>
    <Evidence title="Catalog observation history" files={course.evidence.history || []} description="Observations at scan time; dates do not imply when a catalog change took effect." />
    <details>
      <summary>Selected offering source records</summary>
      <div class="offering-list">
        {#each offerings as offering}
          <article><strong>{offering.course_id} · {termName(offering.term_id)}</strong><p>{offering.title}</p><span class="date">Recorded {offering.observed_at?.slice(0, 10) || "date unavailable"}</span></article>
        {:else}<p class="description">No offering records for the selected term.</p>{/each}
      </div>
      <details class="technical-record"><summary>Raw records</summary><pre>{JSON.stringify(offerings, null, 2)}</pre></details>
    </details>
    {#if course.catalog_variants?.length}<details><summary>Cross-listed catalog records</summary><pre>{JSON.stringify(course.catalog_variants, null, 2)}</pre></details>{/if}
  </section>
  <section class="source-group" aria-label="Review sources">
    <div class="publisher"><MessageSquare size={16} /><span>Rate My Professors</span></div>
    <h3>Student reviews</h3>
    <p class="description">Original comments behind the course and instructor summaries.</p>
    <Evidence title="Read original reviews" files={course.evidence.reviews || []} />
  </section>
  <section class="source-group" aria-label="Grade sources">
    <div class="publisher"><ChartColumn size={16} /><span>Madgrades</span></div>
    <h3>Grade history</h3>
    <p class="description">Recorded grade distributions by term, section, and instructor.</p>
    <a class="grade-link" href="#grades">Explore recorded grades <ArrowUpRight size={13} /></a>
  </section>
</div>
<div class="dataset-footer">
  <div class="dataset-description"><span>Dataset & model</span><p>{course.observed_at ? `Recorded ${course.observed_at.slice(0, 10)}` : "Versioned course records"}</p></div>
  <a href={`https://huggingface.co/datasets/${repository}`}>View the dataset on Hugging Face <ArrowUpRight size={14} /></a>
</div>
<details class="technical-sources">
  <summary>Model outputs & technical records</summary>
  <div class="model-identity"><span>{course.llm_model || "Model not recorded"}</span><AIDisclaimer model={course.llm_model} revision={course.llm_model_revision} /></div>
  <Evidence title="LLM outputs across runs" files={course.evidence.results || []} downloadOnly />
  <Evidence title="Full model traces" files={course.evidence.traces || []} downloadOnly description="Recorded model configuration, reasoning, and tool conversations." />
  <details><summary>Model & dataset provenance</summary><pre>{JSON.stringify({ model: course.llm_model, model_revision: course.llm_model_revision, task_version: course.llm_task_version, output_id: course.llm_output_id, requirements_status: course.llm_requirements_status, dataset_revision: course.revision, observed_at: course.observed_at }, null, 2)}</pre></details>
</details>

<style>
  .source-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 32px; }
  .source-group { min-width: 0; }
  .publisher { display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: 12px; }
  h3 { font-size: 20px; font-weight: 500; margin: 12px 0 8px; }
  .description { color: var(--muted); font-size: 13px; line-height: 1.65; margin-bottom: 24px; max-width: 45ch; min-height: 3.3em; }
  .grade-link, .dataset-footer a { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; }
  .grade-link { margin-top: 18px; color: var(--muted); }
  .dataset-footer { display: flex; align-items: center; justify-content: space-between; gap: 24px; padding-top: 24px; margin-top: 36px; border-top: 1px solid var(--border); }
  .dataset-description span { font-size: 13px; }
  .dataset-description p, .date { color: var(--muted); font-size: 12px; margin-top: 5px; }
  .technical-sources { margin-top: 18px; }
  .model-identity { display: flex; align-items: center; gap: 8px; font-size: 13px; padding: 16px 0; overflow-wrap: anywhere; }
  .offering-list { display: grid; gap: 20px; padding: 16px 0; font-size: 13px; }
  .offering-list strong { font-weight: 500; }
  .offering-list p { margin: 6px 0; }
  pre { max-height: 320px; overflow: auto; }
  @media (max-width: 800px) { .source-grid { grid-template-columns: 1fr; gap: 32px; } .dataset-footer { align-items: flex-start; flex-direction: column; gap: 12px; } }
</style>
