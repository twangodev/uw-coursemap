<script lang="ts">
  const spokes = Array.from({ length: 16 }, (_, i) => i * 22.5);
</script>

<svg viewBox="0 0 560 440" role="img" aria-labelledby="terrace-title">
  <title id="terrace-title"
    >A red sunburst Terrace chair overlooking Lake Mendota</title
  >
  <defs>
    <pattern
      id="lake-lines"
      width="24"
      height="14"
      patternUnits="userSpaceOnUse"
      ><path d="M0 7h14" stroke="currentColor" stroke-width=".6" /></pattern
    >
    <clipPath id="lake-clip"
      ><path d="M22 196Q130 174 258 193T542 183V340H22Z" /></clipPath
    >
  </defs>
  <g class="lake">
    <path
      d="M22 196Q130 174 258 193T542 183"
      fill="none"
      stroke="currentColor"
    />
    <rect
      x="22"
      y="180"
      width="520"
      height="160"
      fill="url(#lake-lines)"
      clip-path="url(#lake-clip)"
      opacity=".65"
    />
    <path
      d="M20 182q50-14 87-4t86-4q28-7 69 2t95-4q72-10 181 2"
      fill="none"
      stroke="currentColor"
      stroke-width="1.5"
    />
    <path
      d="M430 221h32l-7 6h-19zM446 173v44h-27zM451 185v31h15z"
      fill="var(--bg)"
      stroke="currentColor"
      stroke-linejoin="round"
    />
    <path
      d="M78 249h22l-5 4H83zM90 218v27H75z"
      fill="var(--bg)"
      stroke="currentColor"
    />
  </g>
  <text x="401" y="142" class="lake-label">Lake Mendota</text>
  <path
    class="ground"
    d="M40 378q173-17 446 0"
    fill="none"
    stroke="currentColor"
  />
  <g
    class="chair"
    fill="none"
    stroke="currentColor"
    stroke-linecap="round"
    stroke-linejoin="round"
  >
    <path
      d="M187 213l-17 159M307 213l25 159M183 297l-27 83M312 297l34 83"
      stroke-width="7"
    />
    <path d="M168 346h163M181 282h130" stroke-width="4" />
    <path
      d="M173 279Q246 262 318 279L326 300Q246 316 164 300Z"
      fill="var(--bg)"
      stroke-width="5"
    />
    <path
      d="M172 289q75 16 147 0M181 279l-5 18M195 276l-4 24M210 274l-2 28M225 273v31M241 273v32M257 273v32M273 274l2 29M288 276l4 25M303 278l5 20"
      stroke-width="2"
    />
    <circle cx="246" cy="178" r="86" fill="var(--bg)" stroke-width="6" />
    <circle cx="246" cy="178" r="72" stroke-width="2" />
    {#each spokes as angle}<path
        d="M246 162V94"
        transform={`rotate(${angle} 246 178)`}
        stroke-width="3"
      />{/each}
    <circle cx="246" cy="178" r="17" fill="currentColor" stroke-width="2" />
    <path d="M198 246l-7 29M293 249l7 26" stroke-width="6" />
  </g>
  <g class="annotation"
    ><path d="M363 321h47" stroke="currentColor" /><text x="363" y="343"
      >43.0766° N</text
    ><text x="363" y="360">89.3995° W</text></g
  >
</svg>

<style>
  svg {
    width: 100%;
    height: auto;
    overflow: visible;
  }
  .chair {
    color: var(--accent);
  }
  .lake {
    color: var(--muted);
    opacity: 0.45;
  }
  .ground {
    color: var(--border);
  }
  .lake-label {
    fill: var(--muted);
    font: italic 14px var(--font-sans);
  }
  .annotation {
    color: var(--muted);
    fill: var(--muted);
    font: 10px var(--font-mono);
    opacity: 0.7;
  }
</style>
