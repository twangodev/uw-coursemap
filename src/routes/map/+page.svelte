<!-- src/App.svelte -->
<script lang="ts">
    import { onMount } from 'svelte';
    import maplibregl from 'maplibre-gl';
    import 'maplibre-gl/dist/maplibre-gl.css';
    import { MapboxOverlay } from '@deck.gl/mapbox';
    import {MVTLayer} from "@deck.gl/geo-layers";

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
    };

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

        const allLayers = new Set<string>();

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
                allLayers.add(layerName);
                switch (layerName) {
                    case 'building': return [105,105,105, 128];
                    default:         return [0,0,0,0];
                }
            }
        });

        console.debug("All Available Layers:", Array.from(allLayers).sort());

        const deckOverlay = new MapboxOverlay({
            interleaved: true,
            layers: [
                buildingLayer
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
