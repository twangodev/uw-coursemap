<script lang="ts">
  import { BarChart } from "layerchart";
  import { termName } from "$lib/format";
  import type { GradeProjection } from "$lib/grade-projection";
  let { projection }: { projection: GradeProjection } = $props();
</script>

<section class="projection" aria-labelledby="projection-title">
  <div class="projection-heading">
    <h2 id="projection-title">Looking ahead</h2>
    <span class="projection-badge"
      >Projection · {termName(projection.target)}</span
    >
  </div>
  <div class="projection-grid">
    <div class="projection-copy">
      <p class="projected-gpa">
        {projection.gpa.toFixed(2)} <span>estimated GPA</span>
      </p>
      <p>A projected grade mix if recent grading patterns continue.</p>
      <p class="muted">
        Source terms ranged from <strong
          >{projection.historicalRange[0].toFixed(
            2,
          )}–{projection.historicalRange[1].toFixed(2)} GPA</strong
        >.
      </p>
      {#if projection.backtest}<div class="backtest">
          <span>Past forecast accuracy</span><strong
            >{projection.backtest.gpaError.toFixed(2)} GPA average error</strong
          >
          <p class="muted">
            Tested on {projection.backtest.terms} earlier terms, using only data available
            before each one.
          </p>
        </div>{:else}<p class="muted">
          Not enough earlier terms to measure forecast accuracy.
        </p>{/if}
    </div>
    <div>
      <div class="projection-chart">
        <BarChart
          data={projection.grades}
          x="grade"
          y="percentage"
          c="grade"
          cDomain={["A", "AB", "B", "BC", "C", "D", "F"]}
          cRange={[
            "var(--positive)",
            "var(--positive)",
            "var(--grade-mid)",
            "var(--grade-mid)",
            "var(--grade-mid)",
            "var(--negative)",
            "var(--negative)",
          ]}
          series={[{ key: "percentage", label: "Projected percent" }]}
          height={200}
          props={{ bars: { strokeWidth: 0, radius: 2, fillOpacity: 0.7 } }}
        />
      </div>
      <div class="projection-percentages">
        {#each projection.grades as grade}<div>
            <span>{grade.grade}</span><strong
              >{grade.percentage.toFixed(1)}%</strong
            >
          </div>{/each}
      </div>
    </div>
  </div>
  <details>
    <summary>How this projection works</summary>
    <p>
      A recency-weighted average of {projection.sourceTerms.length}
      {projection.sameSeason ? "same-season" : "recent"} terms ({projection.sourceCount.toLocaleString()}
      letter grades). {projection.sameSeason
        ? ""
        : "Matching seasons receive extra weight."} Each term contributes its grade
      proportions; larger classes do not automatically dominate. Source terms: {projection.sourceTerms
        .map(termName)
        .join(", ")}. The range above describes past terms, not a prediction
      interval. This assumes the course is offered; future instructors,
      policies, and enrollment changes are not known. It does not predict an
      individual student’s grade.
    </p>
    {#if projection.backtest}<p>
        Average distribution error in backtesting: {projection.backtest.mixError.toFixed(
          1,
        )} percentage points of grade-share mass (total variation distance).
      </p>{/if}
  </details>
</section>

<style>
  .projection {
    border-top: 1px solid var(--border);
    padding: 40px 0;
  }
  .projection-heading {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 24px;
    margin-bottom: 40px;
  }
  h2 {
    font-size: 25px;
  }
  .projection-badge {
    font-size: 13px;
    color: var(--muted);
    border: 1px dashed var(--muted);
    padding: 6px 12px;
    border-radius: 4px;
  }
  .projection-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 56px;
  }
  .projected-gpa {
    font-size: 40px;
    letter-spacing: -0.04em;
    margin-bottom: 20px;
  }
  .projected-gpa span {
    font-size: 15px;
    letter-spacing: 0;
    color: var(--muted);
  }
  .projection-copy p {
    line-height: 1.7;
    max-width: 44ch;
  }
  .backtest {
    display: grid;
    gap: 8px;
    margin-top: 28px;
    font-size: 14px;
  }
  .backtest > span {
    color: var(--muted);
    font-size: 13px;
  }
  .backtest strong {
    font-weight: 500;
  }
  .projection-chart {
    height: 210px;
  }
  .projection-percentages {
    display: grid;
    grid-template-columns: repeat(7, minmax(0, 1fr));
    gap: 4px;
    text-align: center;
    margin: 16px 0;
    font-size: 12px;
  }
  .projection-percentages div {
    display: grid;
    gap: 8px;
  }
  .projection-percentages span {
    color: var(--muted);
  }
  .projection-percentages strong {
    font-weight: 500;
  }
  details {
    margin-top: 36px;
    font-size: 13px;
  }
  details p {
    max-width: 85ch;
    line-height: 1.7;
    margin-top: 16px;
  }
  @media (max-width: 760px) {
    .projection-heading {
      align-items: start;
      flex-direction: column;
      gap: 16px;
    }
    .projection-grid {
      grid-template-columns: 1fr;
      gap: 36px;
    }
  }
</style>
