# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important: Svelte 5 Usage

This project uses **Svelte 5**, not Svelte 4. All frontend components must use Svelte 5 syntax and patterns. For LLM-compatible Svelte 5 documentation, see: https://svelte.dev/llms.txt

Key Svelte 5 differences:
- Use **runes** (`$state`, `$derived`, `$effect`, `$props`) instead of traditional reactivity
- Component props are destructured from `$props()` rune
- Event handling uses modern patterns, not legacy `createEventDispatcher`

## Development Commands

### Frontend Development
```bash
# Start development server (includes version generation)
npm run dev

# Type checking
npm run check

# Run tests
npm run test

# Run tests with coverage
npm run coverage

# Code formatting
npm run format

# Build for production (includes version generation)
npm run build

# Run documentation server
npm run docs:dev
```

### Full Stack Development
```bash
# Start search service (requires Docker)
cd search && docker-compose up

# Setup Python environment (first time)
uv sync --locked
uv sync --project search

# Generate course data (Python with uv)
uv run coursemap scrape --semester 1272

# Inspect a source snapshot
uv run coursemap status RUN_ID

# Run search service locally
cd search && uv run python app.py
```

### Important Notes
- Version generation runs automatically before dev/build via `npm run generate`
- **Python services use uv** for dependency management (not pip, pipenv, or conda)
- Search service requires Elasticsearch via Docker Compose
- Scraping, inference, and publication have independent resumable checkpoints
- Tests use Vitest framework with coverage reporting

## Application Architecture

### High-Level Overview
UW Course Map is a **microservice architecture** with three main components:
1. **Frontend**: SvelteKit 5 application (main UI)
2. **Backend**: Flask service for search and dynamic data
3. **Static Assets**: Generated JSON files served via CDN

The application helps University of Wisconsin-Madison students explore 10,000+ courses across 190+ departments through interactive visualizations, prerequisite graphs, and comprehensive search.

### Key Architectural Patterns

#### 1. **Microservice Data Architecture**
- **Static API**: Generated JSON files served from CDN (courses, instructors, prerequisites)
- **Search Service**: Flask + Elasticsearch for dynamic course search
- **Data Generation**: Python pipeline with source snapshots, LLM enrichment, and Parquet publication
- **Environment Variables**: Multi-service configuration (`PUBLIC_API_URL`, `PUBLIC_SEARCH_API_URL`)

#### 2. **Data Generation Pipeline**
Run manually from the project root with `uv run coursemap`:

1. Scrapy collects and freezes a source snapshot.
2. `enrich` adds structured metadata through a separately managed inference server.
3. `release` assembles immutable history and relational Parquet tables.
4. `publish --parquet-only` uploads the dataset to Hugging Face.

Website graphs, static JSON exports, and embedding-based graph pruning are retired.
The Worker will consume Parquet and own search and serving.

Active Python code lives in `generation/uw_coursemap`. Historical snapshot readers
remain necessary for full-history exports. See `generation/README.md` for commands.

#### 3. **Routing & Pages**
- **File-based routing**: SvelteKit conventions with `+page.svelte` files
- **Dynamic routes**: `[courseIdentifier]` and `[name]` for courses/instructors
- **Key routes**: `/explorer` (main discovery), `/courses/[id]`, `/instructors/[name]`

#### 4. **Component Organization**
- **UI Primitives**: Comprehensive design system in `lib/components/ui/`
- **Feature Components**: Grouped by functionality (course/, charts/, cytoscape/, map/)
- **Svelte 5 Patterns**: Uses runes system (`$state`, `$derived`, `$props`)

#### 5. **Visualization Stack**
- **Graph Visualization**: Cytoscape.js for prerequisite relationships
- **Map Visualization**: MapLibre GL + Deck.gl for campus buildings and trips
- **Charts**: D3-scale for data visualization
- **Interactive Elements**: Complex state management for graph interactions

#### 6. **Modern Svelte 5 Implementation**
- **Runes System**: `$state`, `$derived`, `$effect` for reactive state
- **TypeScript**: Comprehensive typing throughout
- **Component Composition**: `children` prop patterns for flexible layouts

### Critical Technical Details

#### Data Flow & API Structure
1. **Static API**: RESTful JSON endpoints (`/course/{courseCode}.json`, `/subjects.json`, `/terms.json`)
2. **Server-side loading**: SvelteKit `+page.ts` files with load functions
3. **Client-side fetching**: Dynamic search and real-time interactions
4. **CDN caching**: Cloudflare with 5-day TTL, 70% cache hit rate

#### Key Data Models
- **CourseReference**: Composite object with subjects array and course number
- **CoursePrerequisiteAbstractSyntaxTree**: Complex nested prerequisite structure
- **GradeData**: Comprehensive grade statistics with instructor mappings
- **EnrollmentData**: Term-specific enrollment metadata

#### Build System & Performance
- **Vite**: Primary build tool with custom configuration
- **Adapter-node**: For Node.js deployment
- **Version Generation**: Custom script generates build metadata
- **TailwindCSS 4**: Latest version with utility-first approach
- **Caching Strategy**: 90-98% generation time reduction through platform-dependent caching

#### LLM Enrichment
- Qwen runs in a separately managed vLLM environment.
- The local pipeline requests structured metadata, prerequisite trees, and cited summaries.
- Full traces and pinned model revisions are archived in the dataset.

### Development Workflow & Standards
- Uses [trunk-based development](https://trunkbaseddevelopment.com/)
- Feature branches should be short-lived (1-2 days max)
- Make small, focused changes
- Always ensure `main` is deployable

#### Commit Message Standards
- Be specific and descriptive (avoid single words like "fix" or "update")
- Describe what the commit does, not how it does it
- AI-generated code should include Co-authored-by trailers
- Claude automatically adds `Co-authored-by: Claude <noreply@anthropic.com>`

### Scale & Performance Context
- **600+ peak daily active users**
- **150K+ peak requests per day**
- **75GB+ data served per month**
- **70% cache hit rate** via Cloudflare CDN
- **Cost optimization**: $100 → $15/month through caching strategies

### Project Context
This is a course discovery tool for UW-Madison's 10,000+ courses across 190+ departments. The application focuses on helping students understand course relationships through interactive prerequisite graphs, campus building visualization, and comprehensive search functionality.

The architecture supports high-scale usage with aggressive caching, CDN optimization, and microservice separation for optimal performance and cost efficiency.