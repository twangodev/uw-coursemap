<script lang="ts">
  import CourseList from "$lib/components/CourseList.svelte";
  import { termName } from "$lib/format";
  let { data } = $props();
</script>

<svelte:head><title>UW Courses — Find your next class</title></svelte:head>
<section class="hero">
  <p class="eyebrow">
    University of Wisconsin–Madison · {termName(data.status.term)}
  </p>
  <h1>Find your next class.</h1>
  <p class="muted reading">
    Explore what you’ll learn, who teaches it, and what students have to say.
  </p>
  <form action="/search" class="row">
    <label class="sr-only" for="home-search">Search courses or topics</label
    ><input
      id="home-search"
      class="searchbox"
      name="q"
      placeholder="A course, a topic, something you’re curious about…"
    /><button class="button-primary">Find courses →</button>
  </form>
  <p class="mono muted">
    {data.status.courses.toLocaleString()} courses · {data.status.current_instructors.toLocaleString()}
    current instructors
  </p>
</section>
<section class="section">
  <div class="row between">
    <h2>A few places to start</h2>
    <a href="/search">All courses →</a>
  </div>
  <CourseList courses={data.courses} />
</section>
<section class="section">
  <div class="row between">
    <h2>Browse departments</h2>
    <a href="/subjects">All departments →</a>
  </div>
  <div class="grid departments">
    {#each data.status.departments.slice(0, 18) as d}<a
        class="row between"
        href={"/subjects/" + encodeURIComponent(d.subject)}
        ><span>{d.subject}</span><span class="mono muted">{d.count}</span></a
      >{/each}
  </div>
</section>

<style>
  form {
    max-width: 800px;
  }
  form input {
    flex: 1;
    min-width: 240px;
  }
  .departments {
    margin-top: 1.5rem;
  }
</style>
