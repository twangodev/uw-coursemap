<!-- src/App.svelte -->
<script lang="ts">
    import { onMount } from 'svelte';
    import maplibregl from 'maplibre-gl';
    import 'maplibre-gl/dist/maplibre-gl.css';
    import { MapboxOverlay } from '@deck.gl/mapbox';
    import {MVTLayer} from "@deck.gl/geo-layers";
    import {GeoJsonLayer} from "deck.gl";
    import {_TerrainExtension as TerrainExtension} from "@deck.gl/extensions";
    import { scaleLog } from 'd3-scale';
    import { Slider } from "$lib/components/ui/slider";

    let timeIndex = $state(0);
    let metadata: any = null;
    let isPlaying = $state(false);
    let playInterval: NodeJS.Timeout | null = null;

    // Helper function to format timestamp with timezone
    function formatDateTime(timeIndex: number): { time: string, date: string, timezone: string, hour: number, minute: number } {
        if (!metadata) return { time: '--:--', date: '--/--', timezone: '', hour: 0, minute: 0 };
        
        const startTime = metadata.start_time;
        const chunkDuration = metadata.chunk_duration_minutes;
        const currentTimestamp = startTime + (timeIndex * chunkDuration * 60 * 1000);
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

    // Play/pause functionality
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
                    // Reset to beginning when reaching end
                    timeIndex = 0;
                } else {
                    timeIndex += 1;
                }
                renderFunction?.(timeIndex);
            }, 250); // Play at 2fps (500ms per frame)
        }
    }

    // Get current statistics
    function getCurrentStats(timeIndex: number) {
        if (!metadata) return { persons: 0, instructors: 0 };
        
        return {
            persons: metadata.total_persons?.[timeIndex] || 0,
            instructors: metadata.total_instructors?.[timeIndex] || 0
        };
    }

    const INITIAL_VIEW_STATE = {
        longitude: -89.4012,
        latitude: 43.0731,
        zoom: 15,    // zoom in a bit so buildings pop
        pitch: 45,
        bearing: 0
    };

    let map: maplibregl.Map;

    type PropertiesType = {
        layerName: string,
        render_height?: number;
        colour?: string;
    };

    type BuildingProperties = {
        person_count?: number;
        [key: string]: any;
    };

    // Color scale will be created dynamically based on data
    let colorScale: ReturnType<typeof scaleLog<number>>;
    let deckOverlay: MapboxOverlay;

    let renderFunction: (time: number) => void;
    onMount(async () => {
        map = new maplibregl.Map({
            container: 'map',
            style: 'https://basemaps.cartocdn.com/gl/dark-matter-nolabels-gl-style/style.json',
            center: [INITIAL_VIEW_STATE.longitude, INITIAL_VIEW_STATE.latitude],
            zoom: INITIAL_VIEW_STATE.zoom,
            pitch: INITIAL_VIEW_STATE.pitch,
            bearing: INITIAL_VIEW_STATE.bearing,
        });

        await map.once('load');

        const tileUrls = (map.getStyle().sources.carto as any).url as string

        console.log(map.getStyle())

        const BUILDING_DATA =
            'http://127.0.0.1:5000/highlight/06-30-25';

        const buildingLayer = new MVTLayer<PropertiesType>({
            id: 'buildings-mvt',
            data: tileUrls,
            minZoom: 14,
            maxZoom: 20,
            extruded: true,
            getElevation: f => {
                return (f.properties.render_height || 0) * 2;
            },
            getFillColor: f => {
                const layerName = f.properties.layerName;
                switch (layerName) {
                    case 'building': return [105,105,105, 128];
                    default:         return [0,0,0,0];
                }
            },
            operation: 'terrain+draw'
        });

        // Fetch GeoJSON data to get metadata
        const response = await fetch(BUILDING_DATA);
        const geoJsonData = await response.json();
        
        // Store metadata for reactive updates
        metadata = geoJsonData.metadata;
        
        // Extract max_persons from metadata to set domain
        const maxPersons = metadata?.max_persons || 10_000;
        console.log('Max persons from metadata:', maxPersons);
        
        // Create log scale based on actual data range
        colorScale = scaleLog<number>()
            .domain([1, maxPersons])
            .range([50, 255])
            .clamp(true);


        deckOverlay = new MapboxOverlay({
            interleaved: true,
        })


        function render(time: number) {
            let layers = [
                buildingLayer,
                new GeoJsonLayer({
                    id: 'buildings',
                    data: geoJsonData,
                    extensions: [new TerrainExtension()],
                    stroked: false,
                    filled: true,
                    getFillColor: ({properties}: {properties: BuildingProperties}) => {
                        const personCount = properties.person_counts[timeIndex] || 0;
                        if (personCount === 0) {
                            return [0, 0, 0, 0]; // Transparent for no meetings
                        }

                        // Use d3 log scale to map meeting count to red intensity
                        const redValue = Math.floor(colorScale(personCount));

                        return [redValue, 0, 0, 255]; // Red with alpha
                    },
                    opacity: 0.2,
                    pickable: true,
                    updateTriggers: {
                        getFillColor: time
                    }
                })
            ]

            deckOverlay.setProps({
                layers: layers,
                getCursor: ({isHovering}) => isHovering ? 'pointer' : 'grab',
                onClick: ({object}) => {
                    if (object) {
                        console.log('Clicked object:', object);
                    }
                }
            });
        }

        map.addControl(deckOverlay);

        render(timeIndex)
        renderFunction = render;

    });
</script>

<div class="relative grow">
    <div id="map" class="relative h-full w-full"></div>
    
    <!-- Video-style control bar -->
    <div class="absolute bottom-6 left-1/2 transform -translate-x-1/2 bg-black/60 backdrop-blur-md rounded-full px-6 py-3 flex items-center gap-4">
        <!-- Play Button -->
        <button 
            onclick={togglePlay}
            class="flex items-center justify-center w-8 h-8 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
        >
            {#if isPlaying}
                <!-- Pause icon -->
                <svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
                </svg>
            {:else}
                <!-- Play icon -->
                <svg class="w-4 h-4 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z"/>
                </svg>
            {/if}
        </button>
        
        <!-- Time and Date -->
        <div class="flex flex-col items-center min-w-20">
            <div class="text-white font-mono text-sm">
                {formatDateTime(timeIndex).time}
            </div>
            <div class="text-gray-300 text-xs">
                {formatDateTime(timeIndex).date} {formatDateTime(timeIndex).timezone}
            </div>
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
