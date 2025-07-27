<script lang="ts">
	import {onMount, onDestroy, type Snippet} from 'svelte';
	import maplibregl from 'maplibre-gl';
	import 'maplibre-gl/dist/maplibre-gl.css';
	import { MapboxOverlay } from '@deck.gl/mapbox';
	import { MVTLayer } from '@deck.gl/geo-layers';
	import { GeoJsonLayer, type Layer } from 'deck.gl';
	import { _TerrainExtension as TerrainExtension } from '@deck.gl/extensions';
	import { scaleLog } from 'd3-scale';

	// Props
	interface Props {
		highlightsData: any;
		currentTime: number; // Unix timestamp in milliseconds
		children?: Snippet;
	}

	let { highlightsData, currentTime: highlightTimestamp, children }: Props = $props();

	// State variables
	let map: maplibregl.Map;
	let colorScale: ReturnType<typeof scaleLog<number>>;
	let deckOverlay: MapboxOverlay;
	let mapContainer: HTMLElement;

	// Type definitions
	type PropertiesType = {
		layerName: string;
		render_height?: number;
		colour?: string;
	};

	type BuildingProperties = {
		person_counts?: number[];
		[key: string]: any;
	};

	// Constants
	const INITIAL_VIEW_STATE = {
		longitude: -89.41033202860592,
		latitude: 43.073525483485824,
		zoom: 14.75,
		pitch: 45,
		bearing: 0
	};

	// Setup color scale from highlights data
	function setupColorScale() {
		if (highlightsData?.metadata) {
			const maxPersons = highlightsData.metadata.max_persons || 10_000;
			colorScale = scaleLog<number>().domain([1, maxPersons]).range([50, 255]).clamp(true);
		}
	}

	// Convert Unix timestamp to array index for highlights data
	function timestampToHighlightIndex(timestamp: number): number {
		if (!highlightsData?.metadata) {
			return 0; // Fallback if no metadata
		}
		
		const { start_time, chunk_duration_minutes = 5, total_chunks = 192 } = highlightsData.metadata;
		
		if (!start_time) {
			return 0; // Fallback if no start time
		}
		
		// Calculate the index based on timestamp
		const chunkDurationMs = chunk_duration_minutes * 60 * 1000;
		const index = Math.floor((timestamp - start_time) / chunkDurationMs);
		
		// Clamp to valid range [0, total_chunks - 1]
		return Math.max(0, Math.min(index, total_chunks - 1));
	}


	function render(highlightTimeSlice: number) {
		const layers: Layer[] = [];

		// Add building base layer
		const tileUrls = (map.getStyle().sources.carto as any).url as string;
		const buildingLayer = new MVTLayer<PropertiesType>({
			id: 'buildings-mvt',
			data: tileUrls,
			minZoom: 14,
			maxZoom: 20,
			extruded: true,
			getElevation: (f) => (f.properties.render_height || 0) * 2,
			getFillColor: (f) => {
				const layerName = f.properties.layerName;
				switch (layerName) {
					case 'building':
						return [105, 105, 105, 128];
					default:
						return [0, 0, 0, 0];
				}
			},
			operation: 'terrain+draw'
		});
		layers.push(buildingLayer);

		// Add highlights layer if data is available
		if (highlightsData && colorScale) {
			const highlightsLayer = new GeoJsonLayer({
				id: 'highlights',
				data: highlightsData,
				extensions: [new TerrainExtension()],
				stroked: false,
				filled: true,
				getFillColor: ({ properties }: { properties: BuildingProperties }) => {
					// Use highlight time slice to get the correct value from person_counts array
					const intensity = properties.person_counts?.[highlightTimeSlice] || properties.intensity || 0;
					if (intensity === 0) {
						return [0, 0, 0, 0];
					}
					const redValue = Math.floor(colorScale(intensity));
					return [redValue, 0, 0, 255];
				},
				opacity: 0.2,
				pickable: true,
				updateTriggers: {
					getFillColor: highlightTimeSlice
				}
			});
			layers.push(highlightsLayer);
		}

		deckOverlay.setProps({ layers });
	}

	// Map initialization
	onMount(async () => {
		map = new maplibregl.Map({
			container: mapContainer,
			style: 'https://basemaps.cartocdn.com/gl/dark-matter-nolabels-gl-style/style.json',
			center: [INITIAL_VIEW_STATE.longitude, INITIAL_VIEW_STATE.latitude],
			zoom: INITIAL_VIEW_STATE.zoom,
			pitch: INITIAL_VIEW_STATE.pitch,
			bearing: INITIAL_VIEW_STATE.bearing
		});

		await map.once('load');

		deckOverlay = new MapboxOverlay({
			interleaved: true
		});

		map.addControl(deckOverlay);

		// Setup data from props
		setupColorScale();

		// Initial render
		render(timestampToHighlightIndex(highlightTimestamp));
	});

	onDestroy(() => {
		if (map) {
			map.remove();
		}
	});

	// Reactive statement to update when highlights data changes
	$effect(() => {
		if (highlightsData && map) {
			setupColorScale();
			render(timestampToHighlightIndex(highlightTimestamp));
		}
	});

	// Reactive statement to re-render when highlightTimestamp changes
	$effect(() => {
		if (deckOverlay) {
			render(timestampToHighlightIndex(highlightTimestamp));
		}
	});
</script>

<div class="relative grow">
	<div bind:this={mapContainer} class="relative h-full w-full"></div>
	
	<!-- Render children as absolute overlays -->
	{#if children}
		<div class="absolute inset-0 pointer-events-none">
			{@render children()}
		</div>
	{/if}
</div>