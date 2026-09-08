<script lang="ts">
  import {
    courseUrl,
    credits,
    courseTitle,
    instructorUrl,
    termName,
  } from "$lib/format";
  import type { CourseCard } from "$lib/types";
  import Claims from "./Claims.svelte";
  import AnimatedNumber from "./AnimatedNumber.svelte";
  let { courses, rankStart }: { courses: CourseCard[]; rankStart?: number } = $props();
  const colors = [
    "var(--positive)",
    "var(--positive)",
    "var(--muted)",
    "var(--muted)",
    "var(--negative)",
    "var(--negative)",
    "var(--negative)",
  ];
</script>

<div class="course-results">
  {#each courses as c, index}
    {#if c.discovery}{@const d = c.discovery}
      <article class="discovery-card">
        <div class="card-heading">
          <a href={courseUrl(c.course_uid)}
            ><span class="code">{#if rankStart}<span class="muted">#{rankStart + index} · </span>{/if}{c.course_id}</span>
            <h3>{courseTitle(c.title)}</h3></a
          ><span class="credits">{credits(c.credits_min, c.credits_max)}</span>
        </div>
        {#if c.description}<p class="catalog-description">{c.description}</p>{/if}
        <p class="offering">
          {d.offered
            ? `Offering recorded · ${termName(d.term)}`
            : `No offering record · ${termName(d.term)}`}
        </p>
        {#if d.claim}<div class="takeaway">
            <Claims claims={[d.claim]} reviewFiles={d.reviewFiles} />
          </div>{/if}
        {#if d.instructorHistory?.count}<p class="instructor-comparison">
            <strong
              ><AnimatedNumber
                value={d.instructorHistory.gpa}
                decimals={2}
              /></strong
            >
            with this instructor · <AnimatedNumber
              value={d.courseComparison?.gpa ?? null}
              decimals={2}
            /> course overall, matching historical terms
          </p>{/if}
        <div class="card-bottom">
          <div class="teachers">
            {#each d.instructors.slice(0, 2) as i}<a href={instructorUrl(i.uid)}
                >{courseTitle(i.name || "Unknown instructor")}</a
              >{/each}{#if d.instructors.length > 2}<span class="muted"
                >+{d.instructors.length - 2} more</span
              >{/if}
          </div>
          {#if d.history.count}<div class="history">
              <div
                class="grade-strip"
                role="img"
                aria-label={d.history.counts
                  .map(
                    (n, i) =>
                      `${["A", "AB", "B", "BC", "C", "D", "F"][i]} ${Math.round((n / d.history.count) * 100)}%`,
                  )
                  .join(", ")}
              >
                {#each d.history.counts as n, i}<span
                    style:width={`${(n / d.history.count) * 100}%`}
                    style:background={colors[i]}
                  ></span>{/each}
              </div>
              <p>
                <strong
                  ><AnimatedNumber value={d.history.gpa} decimals={2} /></strong
                >
                historical GPA · <AnimatedNumber value={d.history.count} /> grades
              </p>
              <small
                >{termName(d.history.firstTerm)}–{termName(
                  d.history.lastTerm,
                )}{d.history.count < 100 ? " · limited sample" : ""}</small
              >
            </div>{:else}<p class="muted">No recorded grade history</p>{/if}
        </div>
      </article>
    {:else}<a class="course-row" href={courseUrl(c.course_uid)}
        ><span class="code">{c.course_id}</span><span
          class="course-title"
          title={c.title}>{courseTitle(c.title)}{#if c.description}<span class="catalog-description">{c.description}</span>{/if}</span
        ><span class="muted mono"
          >{credits(c.credits_min, c.credits_max)}{c.gpa != null
            ? ` · ${c.gpa.toFixed(2)} GPA`
            : ""}</span
        ></a
      >{/if}
  {:else}<p class="empty">
      No courses match this selection. Try the full catalog or another term.
    </p>{/each}
</div>

<style>
  .course-results {
    display: grid;
    gap: 24px;
  }
  .discovery-card {
    padding: 26px 0;
    border-bottom: 1px solid var(--border);
    min-width: 0;
  }
  .card-heading {
    display: flex;
    justify-content: space-between;
    align-items: start;
    gap: 24px;
  }
  .card-heading a {
    color: var(--text);
    text-decoration: none;
  }
  .code {
    color: var(--accent);
    font-size: 12px;
  }
  h3 {
    font-size: 23px;
    font-weight: 500;
    margin: 7px 0 0;
    line-height: 1.25;
  }
  .catalog-description { display: -webkit-box; -webkit-line-clamp: 3; line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; max-width: 75ch; margin: 14px 0 0; color: var(--muted); font-size: 14px; font-weight: 400; line-height: 1.65; }
  .credits,
  .offering {
    font-size: 12px;
    color: var(--muted);
  }
  .credits {
    white-space: nowrap;
  }
  .offering {
    margin-top: 10px;
  }
  .takeaway {
    margin: 20px 0;
    max-width: 70ch;
    font-size: 14px;
  }
  .instructor-comparison {
    font-size: 12px;
    color: var(--muted);
    margin-top: 20px;
  }
  .card-bottom {
    display: flex;
    justify-content: space-between;
    align-items: end;
    gap: 24px;
    margin-top: 22px;
  }
  .teachers {
    display: flex;
    flex-wrap: wrap;
    gap: 8px 16px;
    font-size: 13px;
  }
  .history {
    flex-shrink: 0;
    font-size: 12px;
    min-width: 210px;
  }
  .history p {
    margin: 8px 0 4px;
  }
  .history small {
    color: var(--muted);
    font-size: 11px;
  }
  .grade-strip {
    display: flex;
    gap: 2px;
    height: 5px;
    border-radius: 3px;
    overflow: hidden;
    opacity: 0.75;
  }
  @media (max-width: 600px) {
    .card-bottom {
      align-items: start;
      flex-direction: column;
    }
    .history {
      width: 100%;
    }
    .card-heading {
      gap: 12px;
    }
    h3 {
      font-size: 21px;
    }
  }
</style>
