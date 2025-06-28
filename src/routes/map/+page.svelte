<!-- src/App.svelte -->
<script lang="ts">
    import { onMount } from 'svelte';
    import maplibregl from 'maplibre-gl';
    import 'maplibre-gl/dist/maplibre-gl.css';
    import { MapboxOverlay } from '@deck.gl/mapbox';
    import {MVTLayer} from "@deck.gl/geo-layers";
    import {GeoJsonLayer} from "deck.gl";
    import {_TerrainExtension as TerrainExtension} from "@deck.gl/extensions";
    import {scaleLinear, scaleLog} from 'd3-scale';

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
            'http://127.0.0.1:5000/map';

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
        
        // Extract max_meetings from metadata to set domain
        const maxMeetings = geoJsonData.metadata?.max_persons || 10_000;
        console.log('Max meetings from metadata:', maxMeetings);
        
        // Create log scale based on actual data range
        colorScale = scaleLog<number>()
            .domain([1, maxMeetings])
            .range([50, 255])
            .clamp(true);

        const deckOverlay = new MapboxOverlay({
            interleaved: true,
            layers: [
                buildingLayer,
                new GeoJsonLayer({
                    id: 'buildings',
                    data: geoJsonData,
                    extensions: [new TerrainExtension()],
                    stroked: false,
                    filled: true,
                    getFillColor: ({properties}: {properties: BuildingProperties}) => {
                        const personCount = properties.person_count || 0;
                        if (personCount === 0) {
                            return [0, 0, 0, 0]; // Transparent for no meetings
                        }
                        
                        // Use d3 log scale to map meeting count to red intensity
                        const redValue = Math.floor(colorScale(personCount));
                        
                        return [redValue, 0, 0, 255]; // Red with alpha
                    },
                    opacity: 0.2,
                    pickable: true
                })
            ]
        })

        map.addControl(deckOverlay);

        // map.addLayer({
        //     id: '3d-buildings',
        //     // replace `openmaptiles` below with the actual source name you see in your style
        //     source: 'carto',
        //     'source-layer': 'building',
        //     type: 'fill-extrusion',
        //     minzoom: 0,
        //     paint: {
        //         'fill-extrusion-color': '#666',
        //         // use the feature’s `height` property if present,
        //         // otherwise fall back to `levels * 3m`,
        //         // or a static default of 10m
        //         'fill-extrusion-height': [
        //             'coalesce',
        //             ['*', ['get', 'render_height'], 2],
        //             10
        //         ],
        //         // use the feature’s `min_height` if present
        //         'fill-extrusion-base': ['coalesce', ['get', 'render_min_height'], 0],
        //         'fill-extrusion-opacity': 0.5
        //     }
        // });
    });
</script>

<div id="map" class="relative grow"></div>
