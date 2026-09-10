<script lang="ts">
  let { phase = "day" } = $props<{ phase?: string }>();
  const id = $props.id();
  const spokes = Array.from({ length: 28 }, (_, i) => (i * 360) / 28);
</script>

<svg
  viewBox="0 0 600 470"
  role="img"
  aria-label="A red sunburst Terrace chair by Lake Mendota"
  class:night={phase === "night"}
  class:golden={phase === "sunset" || phase === "dawn"}
>
  <defs>
    <linearGradient id={`${id}-sky`} x2="0" y2="1"
      ><stop stop-color="var(--sky-top)" /><stop
        offset="1"
        stop-color="var(--sky-bottom)"
      /></linearGradient
    >
    <linearGradient id={`${id}-water`} x2="0" y2="1"
      ><stop stop-color="var(--water-top)" /><stop
        offset="1"
        stop-color="var(--water-bottom)"
      /></linearGradient
    >
    <linearGradient id={`${id}-chair`} x2="1" y2="1"
      ><stop stop-color="#ed5546" /><stop
        offset="1"
        stop-color="#981e29"
      /></linearGradient
    >
    <clipPath id={`${id}-frame`}
      ><rect x="18" y="18" width="564" height="422" rx="160" /></clipPath
    >
  </defs>
  <g clip-path={`url(#${id}-frame)`}>
    <rect x="18" y="18" width="564" height="422" fill={`url(#${id}-sky)`} />
    <circle class="sun" cx="436" cy="148" r="32" fill="var(--sun)" />
    <g class="stars" fill="#e9e3d5"
      ><circle cx="160" cy="68" r="1.3" /><circle
        cx="346"
        cy="48"
        r="1"
      /><circle cx="484" cy="91" r="1.5" /><circle cx="281" cy="112" r="1" /></g
    >
    <path
      d="M0 229Q65 211 100 219L130 205 155 213 174 207 201 219 236 208 258 216 285 209 311 218 346 202 370 212 390 203 429 216 455 211 486 223 528 208 560 215 600 206V264H0Z"
      fill="var(--shore)"
    />
    <path d="M0 231Q220 225 600 230V395H0Z" fill={`url(#${id}-water)`} />
    <g class="ripples" fill="none" stroke="var(--glint)" stroke-linecap="round">
      <path
        d="M387 248h63m-82 11h106m-73 13h36m-76 13h117m-57 13h42"
        opacity=".65"
      />
      <path
        d="M58 254h46m25 20h51m-98 23h78m346-41h32M299 245h24m-59 64h63m171 14h39M46 328h77"
        opacity=".4"
      />
    </g>
    <g class="boat" transform="translate(345 261)"
      ><path d="M-16 0h35l-7 7H-9Z" fill="var(--shore)" /><path
        d="M2-43V-5H-19Z"
        fill="#e9e2ce"
      /><path d="M7-31V-5h14Z" fill="#bdbba9" /></g
    >
    <path d="M0 365Q240 331 600 366V470H0Z" fill="var(--ground)" />
    <path
      d="M0 392Q240 351 600 389M125 351 62 470M361 350 427 470"
      fill="none"
      stroke="var(--ground-line)"
    />
    <ellipse cx="236" cy="411" rx="104" ry="12" fill="#101715" opacity=".14" />
    <g stroke-linecap="round" stroke-linejoin="round">
      <path
        d="M195 307 173 410M276 304 303 407M191 346 159 404M292 342 322 405M181 385h115"
        fill="none"
        stroke="#8c2429"
        stroke-width="7"
      />
      <path
        d="M182 333Q233 315 291 332L302 348Q244 370 169 349Z"
        fill={`url(#${id}-chair)`}
        stroke="#a82b31"
        stroke-width="4"
      />
      <path
        d="m190 333-6 18m20-23-3 26m19-28-1 31m19-31 1 32m17-30 3 28m14-25 5 22"
        stroke="#73252b"
        opacity=".45"
        stroke-width="2"
      />
      <path d="m191 334 9-81m82 79-13-76" stroke="#b33035" stroke-width="7" />
      <g transform="translate(233 252) rotate(-8) scale(.87 1)">
        <circle r="76" fill="none" stroke="#8e272e" stroke-width="10" />
        <circle r="76" fill="none" stroke="#d74640" stroke-width="6" />
        {#each spokes as angle}<path
            d="M0-14V-72"
            transform={`rotate(${angle})`}
            stroke="#dc4941"
            stroke-width="3.8"
          />{/each}
        <circle r="16" fill="#d74640" /><circle r="9" fill="#e35145" />
      </g>
    </g>
  </g>
</svg>

<style>
  svg {
    width: 100%;
    height: auto;
    --sky-top: #a6c0c0;
    --sky-bottom: #e1dcca;
    --water-top: #688f91;
    --water-bottom: #8da6a0;
    --shore: #4f6b63;
    --sun: #f4e4ad;
    --glint: #d7d9b6;
    --ground: #b7ad97;
    --ground-line: #a19b88;
  }
  .golden {
    --sky-top: #78888f;
    --sky-bottom: #e9b887;
    --water-top: #858e8a;
    --water-bottom: #b0a794;
    --sun: #ffd497;
    --glint: #efd3a0;
    --ground: #a99c8c;
  }
  .night {
    --sky-top: #182b3b;
    --sky-bottom: #425664;
    --water-top: #304f5b;
    --water-bottom: #42616a;
    --shore: #233e40;
    --sun: #eee6cc;
    --glint: #7e9b9d;
    --ground: #565c56;
    --ground-line: #4b524d;
  }
  .stars {
    opacity: 0;
  }
  .night .stars {
    opacity: 0.8;
  }
  .ripples {
    animation: drift 9s ease-in-out infinite alternate;
  }
  .boat {
    animation: bob 6s ease-in-out infinite alternate;
    transform-origin: 345px 261px;
  }
  @keyframes drift {
    to {
      transform: translateX(5px);
    }
  }
  @keyframes bob {
    to {
      translate: 0 2px;
      rotate: 0.6deg;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .ripples,
    .boat {
      animation: none;
    }
  }
</style>
