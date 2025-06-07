# Generation

The generation process is responsible for collecting, aggregating, and analyzing a majority of the data used in the application, including course data, professor ratings, and more. 

> [!TIP] Data Science
> Since the generation process is heavily data-driven, if your interested in performing final analysis on the data, you can check out the [aggregation step](#aggregation) for more details on how the data is collected and processed.

## Process Overview

The generation process can be broken down into several key steps, as implemented in [#71](https://github.com/twangodev/uw-coursemap/pull/71); each step is responsible for a specific part of the data collection and processing pipeline.

You can specify the step to run with the `--step` flag when running the generation command. The steps are as follows:

```bash
pipenv run python generation/main.py --step <step_name> 
```

Where `<step_name>` can be one of the following:

- `all`: Run all steps in order
- `courses`: Run the course collection step 
- `madgrades`: Run the madgrades integration step 
- `instructors`: Run the instructor collection step 
- `aggregate`: Run the aggregation step 
- `optimize`: Run the optimization step
- `graph`: Run the graph step

> [!TIP]
> An additional flag `-nb` or `--no_build` can be used to skip the final build step, which writes cached data to the `DATA_DIR` specified in your environment. This is recommended if you are running the individual steps for debugging or testing purposes.

```mermaid
graph TD
    CC@{ shape: procs, label: "fa:fa-chalkboard Course Collection   "}
    MI@{ shape: procs, label: "fa:fa-graduation-cap Madgrades Integration "}
    IC@{ shape: procs, label: "fa:fa-user-tie Instructor Collection "}
    AG@{ shape: procs, label: "fa:fa-chart-bar Aggregation "}
    OP@{ shape: procs, label: "fa:fa-cogs Optimization "}
    GR@{ shape: procs, label: "fa:fa-project-diagram Graph "}
        
    CC --> MI
    MI --> IC
    IC --> AG
    AG --> OP
    OP --> GR

```

This allows you to debug and test each step independently, while also providing a clear path for data flow through the process.

### Cache

Each of these steps, except for the final build step, write to a unified `.cache` directory, which is used to store intermediate results and final outputs. The final build step compiles all the data into a single output file.

Generally, the cache is platform-dependent* (it contains a models cache used for embeddings), so you should use the same cache for all steps on a single platform.

Additionally, API keys and other sensitive information may be stored in the cache, which bad actors may use, so it is recommended to keep the cache directory secure and not share it publicly.

<small>*This is a hunch, but it is likely that the cache is platform-dependent due to the models used for embeddings and other data processing steps.</small>

### Performance

Generally, this process takes 2-6 hours to run from a dry state, depending on the number of courses and instructors being processed. The time can vary based your system's performance, network speed, and the number of courses and instructors being processed.

As a baseline, we run this process from a dry state on GitHub's CI servers, which takes roughly 3 hours. For context, public CI runners have [4 vCPUs and 16GB of RAM](https://docs.github.com/en/actions/using-github-hosted-runners/using-github-hosted-runners/about-github-hosted-runners#standard-github-hosted-runners-for-public-repositories) available, which is generally equivalent if not worse than a mid-range laptop.

With an existing cache, the process can be significantly faster. GitHub's CI servers have run the entire process in under 3 minutes with a cached state.

Therefore, during development, it is recommended to run the process with a cached state to speed up the development cycle, or run them against our existing CI pipeline. (When you submit a PR, we can manually trigger the generation process to run against your branch, if you request it in the PR description.)

## Steps

### Course Collection

```mermaid
graph LR
    SM["Guide Sitemap<br><small>guide.wisc.edu/sitemap.xml</small>"]
    CC@{ shape: procs, label: "fa:fa-chalkboard Course Collection "}
    SD@{ shape: procs, label: "fa:fa-school Subject/Department Definitions" }
    
    C[(Cache)]
    
    SM --> CC
    SM --> SD
    CC --> C
    SD --> C
```

To dynamically retrieve all courses offered at the University of Wisconsin-Madison, we scrape the [Guide Sitemap](https://guide.wisc.edu/sitemap.xml) to get a list of all courses and their associated departments. We filter by paths that match the pattern `/courses/...` to ensure we only collect courses, and not other types of content.

Next, we take the courses listed on each of the department pages and scrape the course.

![course-breakdown.png](../public/assets/course-breakdown.png)

This is also where we build our Abstract Syntax Tree (AST) for requisites.

> ##### COMPSCI 300 Requisites: 
> 
> Satisfied QR-A and (COMPSCI 200 , COMPSCI 220 , 302, COMPSCI 310 , 301, or placement into COMPSCI 300 ) or (COMPSCI/ECE 252 and ECE 203 ); graduate/professional standing; declared in Capstone Certificate in COMP SCI. Not open to students with credit for COMP SCI 367.
>
> ![ast.png](../public/assets/ast.png)
> 
> We drop branches that include a negation phrase, such as "Not open for students with..."

We also need to address issues of duplicate course listings, as some courses are listed under multiple departments.

![course-reference.png](../public/assets/course-reference.png)

We can use this "Reference" as a unique identifier for each course to prevent duplicates. This allows us to ensure that we only collect each course once, even if it is listed under multiple departments.

### Madgrades Integration

```mermaid
graph TD
    
    subgraph api.madgrades.com
        MT["Madgrades Terms"]
        MPG@{ shape: docs, label: "fa:fa-graduation-cap Madgrades Pagination" }
        MGD@{ shape: procs, label: "fa:fa-graduation-cap Madgrades GradeData" }
        
        MPG ===> MGD
    end
    
    CET["Course Enrollment Terms<br><small>public.enroll.wisc.edu</small>"]
    T[Terms]
    
    MT ---> T
    CET ---> T
    
    C[(Cache)]
    CC@{ shape: procs, label: "fa:fa-chalkboard Course Collection "}

    MGD ---> CC
    T --> C
    CC <--> C
```

Madgrades contains historical data for all courses, including courses not currently offered. We care about the courses that we have collected in the previous step, so we scrape the Madgrades website to get the historical data for those courses. There will also be courses that are newly added to the Guide, but not yet in Madgrades.

Since Madgrades API is paginated, we need to retrieve all the pages of data for each course. From each page, we pull grade data, distribution, and other relevant information.

We additionally retrieve the terms that are available in Madgrades, and the terms that are available in the Course Enrollment Terms API. Madgrades generally will have historical terms (lagging behind the current semester), while the Course Enrollment Terms API will have the current and upcoming terms.

### Instructor Collection

```mermaid
graph TB
    subgraph ratemyprofessors.com
        direction LR
        RMPAPIKEY["RMP API Key"]
        RMPGQL@{ shape: procs, label: "fa:fa-user-tie RMP GraphQL</small>" }
        RMPAPIKEY --> RMPGQL
    end
    
    subgraph wisc.edu

        MQ@{ shape: procs, label: "fa:fa-chalkboard Mega Query<br><small>public.enroll.wisc.edu</small>" }
        FL["Faculty List<br><small>guide.wisc.edu</small>"]
        
    end
    
    C[(Cache)]
    T[Terms]
    
    CC@{ shape: procs, label: "fa:fa-chalkboard Course Collection" }
    IC@{ shape: procs, label: "fa:fa-user-tie Instructor Collection<br><small>Name Matcher</small>" }
    
    C --> T
    T --> MQ
    MQ ===> CC
    CC <--> C
    
    CC --> IC
    FL ---> IC
    RMPGQL <---> IC
    IC --> C
```

The instructor collection step, admittedly, does slightly more than collect instructors. Instructor collection performs the "Mega Query." 

For some reason, the Course Enrollment Terms Search API does not validate two items.

1. `queryString` is not validated, so you can pass in any string, including an empty string, and it will return all courses.
2. `pageSize` is practically not validated, so you can pass in a very large number, and it will return that many results. You cannot pass `99999999`, but you can pass in the total amount of courses in the term, which is given from the `found` field in the response.

It's a feature, not a bug! When this gets patched (if it ever does), we can just paginate through the results and do a bit of de-duplication, kind of like with Madgrades. It's fun that Madgrades, another open source project, validates requests, but UW-Madison does not ;).

With these two facts, we can construct a query that returns all courses in the system.

![mega-query.png](../public/assets/mega-query.png)

We get a hilarious amount of data, ranging from (20MB—40MB), depending on how many courses are offered in a given term.

We take all the data from Enrollment and add it within our existing course collection. This includes course information, such as the course name, description, and more.

Next, we collect the instructors for each course. We do this by scraping the [Faculty List](https://guide.wisc.edu/faculty/) page, which contains a list of all instructors at the University of Wisconsin-Madison.

The thing is, the format of the names is not consistent, and we need to match the names to the instructors in the Course Enrollment Terms API. This is handled with a name matching and diffing technique that compares the names from the Faculty List to the names in the Course Enrollment Terms API, and for the most part, it works well. You may notice issues with instructors being matched to their alternate names, but this seems like one of a couple edge cases.

We combine the data from the Faculty List and the Course Enrollment Terms API to create a unified list of instructors, which includes their names, departments, and other relevant information.

Finally, we also integrate with [Rate My Professors](https://www.ratemyprofessors.com/) to get additional data about the instructors, such as their ratings and reviews. This is done using the Rate My Professors GraphQL API, which allows us to retrieve data about instructors based on their names.

RateMyProfessors has (or had) an authenticated API, where we could send GraphQL queries to retrieve data about instructors. After some digging around, we found that the API key was provided through a JavaScript file that was loaded on the Rate My Professors website. We scrape the JavaScript file to get the production API key, which is then used to authenticate our requests to the Rate My Professors API. This in addition to modifying a couple of headers to make the request look like it is coming from a browser.

### Aggregation

### Optimization

### Graph

### Build

