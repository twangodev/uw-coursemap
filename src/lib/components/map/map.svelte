<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import maplibregl from 'maplibre-gl';
	import 'maplibre-gl/dist/maplibre-gl.css';
	import { MapboxOverlay } from '@deck.gl/mapbox';
	import { MVTLayer } from '@deck.gl/geo-layers';
	import { GeoJsonLayer, type Layer } from 'deck.gl';
	import { _TerrainExtension as TerrainExtension } from '@deck.gl/extensions';
	import { scaleLog } from 'd3-scale';

	// Props
	interface Props {
		highlightsUrl: string;
		children?: import('svelte').Snippet;
	}

	let { highlightsUrl, children }: Props = $props();

	// State variables
	let map: maplibregl.Map;
	let colorScale: ReturnType<typeof scaleLog<number>>;
	let deckOverlay: MapboxOverlay;
	let mapContainer: HTMLElement;
	let currentGeoJsonData = $state<any>(null);

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
		longitude: -89.4012,
		latitude: 43.0731,
		zoom: 15,
		pitch: 45,
		bearing: 0
	};

	// Data loading function
	async function loadHighlightsData() {
		try {
			const response = await fetch(highlightsUrl);
			const geoJsonData = await response.json();
			
			currentGeoJsonData = geoJsonData;

			// Set up color scale if metadata exists
			if (geoJsonData.metadata) {
				const maxPersons = geoJsonData.metadata.max_persons || 10_000;
				colorScale = scaleLog<number>().domain([1, maxPersons]).range([50, 255]).clamp(true);
			}

			// Re-render the map
			if (deckOverlay) {
				render();
			}
		} catch (error) {
			console.warn('Failed to load highlights data:', error);
		}
	}

	function render() {
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
		if (currentGeoJsonData && colorScale) {
			const highlightsLayer = new GeoJsonLayer({
				id: 'highlights',
				data: currentGeoJsonData,
				extensions: [new TerrainExtension()],
				stroked: false,
				filled: true,
				getFillColor: ({ properties }: { properties: BuildingProperties }) => {
					// For static highlights, use first value or a simple property
					const intensity = properties.person_counts?.[0] || properties.intensity || 0;
					if (intensity === 0) {
						return [0, 0, 0, 0];
					}
					const redValue = Math.floor(colorScale(intensity));
					return [redValue, 0, 0, 255];
				},
				opacity: 0.2,
				pickable: true
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

		// Load initial data
		await loadHighlightsData();
	});

	onDestroy(() => {
		if (map) {
			map.remove();
		}
	});

	// Reactive statement to reload data when URL changes
	$effect(() => {
		if (highlightsUrl && map) {
			loadHighlightsData();
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