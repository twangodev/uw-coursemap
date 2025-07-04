<script lang="ts">
	import {onMount, onDestroy, type Snippet} from 'svelte';
	import maplibregl from 'maplibre-gl';
	import 'maplibre-gl/dist/maplibre-gl.css';
	import { MapboxOverlay } from '@deck.gl/mapbox';
	import { MVTLayer } from '@deck.gl/geo-layers';
	import { GeoJsonLayer, TripsLayer, type Layer } from 'deck.gl';
	import { _TerrainExtension as TerrainExtension } from '@deck.gl/extensions';
	import { scaleLog } from 'd3-scale';
	import { animate, useMotionValue } from 'svelte-motion';

	// Props
	interface Props {
		highlightsData: any;
		tripsData: any;
		timeIndex: number;
		children?: Snippet;
	}

	let { highlightsData, tripsData: propsTripsData, timeIndex, children }: Props = $props();

	// State variables
	let map: maplibregl.Map;
	let colorScale: ReturnType<typeof scaleLog<number>>;
	let deckOverlay: MapboxOverlay;
	let mapContainer: HTMLElement;
	let maxTimestamp = $state(0);
	let currentTime = useMotionValue(0);

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

	// Calculate max timestamp from trips data
	function calculateMaxTimestamp() {
		if (!propsTripsData) return;
		
		let max = 0;
		for (const trip of propsTripsData) {
			for (const waypoint of trip.waypoints) {
				if (waypoint.timestamp > max) {
					max = waypoint.timestamp;
				}
			}
		}
		maxTimestamp = max;
	}

	function render(highlightsTime: number, tripTime: number) {
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

		// Add trips layer if data is available
		if (propsTripsData) {
			const tripsLayer = new TripsLayer({
				id: 'TripsLayer',
				data: propsTripsData,
				getPath: (d: any) => {
					const height = Math.floor(Math.random() * 10) + 5;
					return d.waypoints.map((p: any) => {
						const [lon, lat] = p.coordinates;
						return [lon, lat, height];
					});
				},
				getTimestamps: (d: any) => d.waypoints.map((p: any) => p.timestamp),
				getColor: [253, 128, 93],
				currentTime: tripTime,
				trailLength: 110000,
				capRounded: true,
				jointRounded: true,
				widthMinPixels: 2,
				opacity: 0.3,
			});
			layers.push(tripsLayer);
		}

		// Add highlights layer if data is available
		if (highlightsData && colorScale) {
			const highlightsLayer = new GeoJsonLayer({
				id: 'highlights',
				data: highlightsData,
				extensions: [new TerrainExtension()],
				stroked: false,
				filled: true,
				getFillColor: ({ properties }: { properties: BuildingProperties }) => {
					// Use time index to get the correct value from person_counts array
					const intensity = properties.person_counts?.[highlightsTime] || properties.intensity || 0;
					if (intensity === 0) {
						return [0, 0, 0, 0];
					}
					const redValue = Math.floor(colorScale(intensity));
					return [redValue, 0, 0, 255];
				},
				opacity: 0.2,
				pickable: true,
				updateTriggers: {
					getFillColor: highlightsTime
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
		calculateMaxTimestamp();

		currentTime.set(0); // Initialize current time

		// Set up animation loop for trips
		function loop() {
			animate(currentTime, maxTimestamp, {
				duration: 30,
				ease: "linear",
				onComplete: () => {
					currentTime.set(maxTimestamp * 0.1); // Reset to 10% of animation
					loop(); // Restart the animation loop
				}
			});
		}

		// Start the animation loop
		loop();

		// Subscribe to currentTime changes to re-render
		unsubscribeFn = currentTime.subscribe((value) => {
			render(timeIndex, value);
		});

		// Initial render
		render(timeIndex, currentTime.get());
	});

	// Store unsubscribe function for cleanup
	let unsubscribeFn: (() => void) | null = null;

	onDestroy(() => {
		if (unsubscribeFn) {
			unsubscribeFn();
		}
		if (map) {
			map.remove();
		}
	});

	// Reactive statement to update when highlights data changes
	$effect(() => {
		if (highlightsData && map) {
			setupColorScale();
			render(timeIndex, currentTime.get());
		}
	});

	// Reactive statement to update when trips data changes
	$effect(() => {
		if (propsTripsData && map) {
			calculateMaxTimestamp();
			render(timeIndex, currentTime.get());
		}
	});

	// Reactive statement to re-render when timeIndex changes
	$effect(() => {
		if (deckOverlay) {
			render(timeIndex, currentTime.get());
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