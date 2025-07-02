<script lang="ts">
	import { onMount } from 'svelte';
	import maplibregl from 'maplibre-gl';
	import 'maplibre-gl/dist/maplibre-gl.css';
	import { MapboxOverlay } from '@deck.gl/mapbox';
	import { MVTLayer } from '@deck.gl/geo-layers';
	import { GeoJsonLayer, type Position, TripsLayer } from 'deck.gl';
	import { _TerrainExtension as TerrainExtension } from '@deck.gl/extensions';
	import { scaleLog } from 'd3-scale';
	import { Slider } from '$lib/components/ui/slider';
	import { Calendar } from '$lib/components/ui/calendar';
	import { Popover, PopoverContent, PopoverTrigger } from '$lib/components/ui/popover';
	import { DateFormatter, getLocalTimeZone, today } from '@internationalized/date';
	import { animate, useMotionValue } from 'svelte-motion';
	import { env } from '$env/dynamic/public';

	// State variables
	let timeIndex = $state(0);
	let metadata = $state<any>(null);
	let isPlaying = $state(false);
	let playInterval: NodeJS.Timeout | null = null;
	let selectedDate = $state(today(getLocalTimeZone()));
	let selectedJSDate = $state(new Date());
	let currentGeoJsonData = $state<any>(null);
	let calendarOpen = $state(false);
	let tripsData = $state<any>(null);
	let maxTimestamp = $state(0);
	let map: maplibregl.Map;
	let colorScale: ReturnType<typeof scaleLog<number>>;
	let deckOverlay: MapboxOverlay;
	let renderFunction: (time: number) => void;

	// Type definitions
	type Trip = {
		waypoints: {
			coordinates: Position;
			timestamp: number;
		}[];
	};

	type PropertiesType = {
		layerName: string;
		render_height?: number;
		colour?: string;
	};

	type BuildingProperties = {
		person_count?: number;
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

	const df = new DateFormatter('en-US', {
		dateStyle: 'medium'
	});

	// Utility functions
	function formatDateForAPI(date: Date): string {
		const month = String(date.getMonth() + 1).padStart(2, '0');
		const day = String(date.getDate()).padStart(2, '0');
		const year = String(date.getFullYear()).slice(-2);
		return `${month}-${day}-${year}`;
	}

	function formatDateTime(timeIndex: number): {
		time: string;
		date: string;
		timezone: string;
		hour: number;
		minute: number;
	} {
		if (!metadata) return { time: '--:--', date: '--/--', timezone: '', hour: 0, minute: 0 };

		const startTime = metadata.start_time;
		const chunkDuration = metadata.chunk_duration_minutes;
		const currentTimestamp = startTime + timeIndex * chunkDuration * 60 * 1000;
		const date = new Date(currentTimestamp);

		return {
			time: date.toLocaleTimeString('en-US', {
				hour: '2-digit',
				minute: '2-digit',
				hour12: true
			}),
			date: date.toLocaleDateString('en-US', {
				month: 'short',
				day: 'numeric'
			}),
			timezone: date.toLocaleTimeString('en-US', {
				timeZoneName: 'short'
			}).split(' ').pop() || '',
			hour: date.getHours() % 12 || 12,
			minute: date.getMinutes()
		};
	}

	function getCurrentStats(timeIndex: number) {
		if (!metadata) return { persons: 0, instructors: 0 };

		return {
			persons: metadata.total_persons?.[timeIndex] || 0,
			instructors: metadata.total_instructors?.[timeIndex] || 0
		};
	}

	// Control functions
	function togglePlay() {
		if (isPlaying) {
			if (playInterval) {
				clearInterval(playInterval);
				playInterval = null;
			}
			isPlaying = false;
		} else {
			isPlaying = true;
			playInterval = setInterval(() => {
				if (timeIndex >= (metadata?.total_chunks - 1 || 191)) {
					timeIndex = 0;
				} else {
					timeIndex += 1;
				}
				renderFunction?.(timeIndex);
			}, 250);
		}
	}

	async function changeDate(newDate: Date) {
		selectedJSDate = newDate;
		timeIndex = 0;
		isPlaying = false;
		if (playInterval) {
			clearInterval(playInterval);
			playInterval = null;
		}

		const newData = await loadDataForDate(selectedJSDate);
		currentGeoJsonData = newData;

		if (renderFunction) {
			renderFunction(timeIndex);
		}
	}

	// Data loading functions
	async function loadDataForDate(date: Date) {
		const dateStr = formatDateForAPI(date);
		const BUILDING_DATA = `https://static.uwcourses.com/meetings/${dateStr}.geojson`;

		const response = await fetch(BUILDING_DATA);
		const geoJsonData = await response.json();

		metadata = geoJsonData.metadata;

		const maxPersons = metadata?.max_persons || 10_000;
		console.log('Max persons from metadata:', maxPersons);

		colorScale = scaleLog<number>().domain([1, maxPersons]).range([50, 255]).clamp(true);

		return geoJsonData;
	}

	async function loadTripsData() {
		const response = await fetch(`${env.PUBLIC_API_URL}/trips.json`);
		const data = await response.json();
		tripsData = data;

		let max = 0;
		for (const trip of data) {
			for (const waypoint of trip.waypoints) {
				if (waypoint.timestamp > max) {
					max = waypoint.timestamp;
				}
			}
		}
		maxTimestamp = max;
		return data;
	}

	// Map initialization
	onMount(async () => {
		map = new maplibregl.Map({
			container: 'map',
			style: 'https://basemaps.cartocdn.com/gl/dark-matter-nolabels-gl-style/style.json',
			center: [INITIAL_VIEW_STATE.longitude, INITIAL_VIEW_STATE.latitude],
			zoom: INITIAL_VIEW_STATE.zoom,
			pitch: INITIAL_VIEW_STATE.pitch,
			bearing: INITIAL_VIEW_STATE.bearing
		});

		await map.once('load');

		const tileUrls = (map.getStyle().sources.carto as any).url as string;
		console.log(map.getStyle());

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

		currentGeoJsonData = await loadDataForDate(selectedJSDate);
		await loadTripsData();

		deckOverlay = new MapboxOverlay({
			interleaved: true
		});

		function render(time: number, tripTime: number) {
			const trips = new TripsLayer<Trip>({
				id: 'TripsLayer',
				data: tripsData,
				getPath: (d) => {
					const height = Math.floor(Math.random() * 10) + 5;
					return d.waypoints.map((p) => {
						const [lon, lat, alt = 0] = p.coordinates;
						return [lon, lat, height];
					});
				},
				getTimestamps: (d) => d.waypoints.map((p) => p.timestamp),
				getColor: [253, 128, 93],
				currentTime: tripTime,
				trailLength: 110000,
				capRounded: true,
				jointRounded: true,
				widthMinPixels: 2,
				opacity: 0.3
			});

			const layers = [
				trips,
				buildingLayer,
				new GeoJsonLayer({
					id: 'buildings',
					data: currentGeoJsonData,
					extensions: [new TerrainExtension()],
					stroked: false,
					filled: true,
					getFillColor: ({ properties }: { properties: BuildingProperties }) => {
						const personCount = properties.person_counts[timeIndex] || 0;
						if (personCount === 0) {
							return [0, 0, 0, 0];
						}

						const redValue = Math.floor(colorScale(personCount));
						return [redValue, 0, 0, 255];
					},
					opacity: 0.2,
					pickable: true,
					updateTriggers: {
						getFillColor: time
					}
				})
			];

			deckOverlay.setProps({
				layers
			});
		}

		map.addControl(deckOverlay);

		const currentTime = useMotionValue(0);

		function loop() {
			animate(currentTime, maxTimestamp, {
				duration: 30,
				ease: 'linear',
				onComplete: () => {
					currentTime.set(0);
					loop();
				}
			});
		}

		render(timeIndex, currentTime.get());
		renderFunction = (time: number) => {
			const tripTime = currentTime.get();
			render(time, tripTime);
		};

		loop();

		const unsubscribe = currentTime.subscribe((value) => {
			render(timeIndex, value);
		});
	});
</script>

<div class="relative grow">
	<div id="map" class="relative h-full w-full"></div>

	<!-- Video-style control bar -->
	<div
		class="absolute bottom-6 left-1/2 transform -translate-x-1/2 bg-black/60 backdrop-blur-md rounded-full px-6 py-3 flex items-center gap-4"
	>
		<!-- Play Button -->
		<button
			onclick={togglePlay}
			class="flex items-center justify-center w-8 h-8 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
		>
			{#if isPlaying}
				<!-- Pause icon -->
				<svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
					<path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
				</svg>
			{:else}
				<!-- Play icon -->
				<svg class="w-4 h-4 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
					<path d="M8 5v14l11-7z" />
				</svg>
			{/if}
		</button>

		<!-- Time and Date with Calendar Popover -->
		<div class="flex flex-col items-center min-w-20">
			<div class="text-white font-mono text-sm">
				{formatDateTime(timeIndex).time}
			</div>
			<Popover bind:open={calendarOpen}>
				<PopoverTrigger>
					<button
						class="text-gray-300 text-xs hover:text-white transition-colors cursor-pointer"
					>
						{formatDateTime(timeIndex).date}
					</button>
				</PopoverTrigger>
				<PopoverContent class="w-auto p-4" align="center" side="top">
					<Calendar
						type="single"
						bind:value={selectedDate}
						captionLayout="dropdown"
						onValueChange={(value) => {
							if (value) {
								selectedJSDate = new Date(value.year, value.month - 1, value.day);
								changeDate(selectedJSDate);
								calendarOpen = false;
							}
						}}
					/>
					<div class="text-center mt-3 pt-3 border-t">
						<p class="text-xs text-muted-foreground">
							All times displayed in {Intl.DateTimeFormat().resolvedOptions().timeZone}
						</p>
					</div>
				</PopoverContent>
			</Popover>
		</div>

		<!-- Slider -->
		<div class="flex-1 min-w-64">
			<Slider
				type="single"
				bind:value={timeIndex}
				max={metadata?.total_chunks - 1 || 191}
				onValueChange={() => {
					renderFunction?.(timeIndex);
				}}
			/>
		</div>

		<!-- Statistics -->
		<div class="flex gap-4 text-xs">
			<div class="flex flex-col items-center">
				<div class="text-blue-300 font-semibold">
					{getCurrentStats(timeIndex).persons.toLocaleString()}
				</div>
				<div class="text-gray-400">Persons</div>
			</div>
			<div class="flex flex-col items-center">
				<div class="text-green-300 font-semibold">
					{getCurrentStats(timeIndex).instructors.toLocaleString()}
				</div>
				<div class="text-gray-400">Instructors</div>
			</div>
		</div>
	</div>
</div>