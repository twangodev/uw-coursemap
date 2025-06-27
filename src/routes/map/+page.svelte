<!-- src/App.svelte -->
<script>
    import { onMount } from 'svelte';
    import maplibregl from 'maplibre-gl';
    import 'maplibre-gl/dist/maplibre-gl.css';

    const INITIAL_VIEW_STATE = {
        longitude: -74,
        latitude: 40.72,
        zoom: 15,    // zoom in a bit so buildings pop
        pitch: 45,
        bearing: 0
    };

    let map;

    onMount(() => {
        map = new maplibregl.Map({
            container: 'map',
            style:
                'https://basemaps.cartocdn.com/gl/dark-matter-nolabels-gl-style/style.json',
            center: [INITIAL_VIEW_STATE.longitude, INITIAL_VIEW_STATE.latitude],
            zoom: INITIAL_VIEW_STATE.zoom,
            pitch: INITIAL_VIEW_STATE.pitch,
            bearing: INITIAL_VIEW_STATE.bearing
        });

        map.on('load', () => {
            // (Optional) inspect your style’s sources to find the vector‐tile source name:
            // console.log(Object.keys(map.getStyle().sources));

            map.addLayer({
                id: '3d-buildings',
                // replace `openmaptiles` below with the actual source name you see in your style
                source: 'carto',
                'source-layer': 'building',
                type: 'fill-extrusion',
                minzoom: 0,
                paint: {
                    // building color
                    'fill-extrusion-color': '#666',
                    // use the feature’s `height` property if present,
                    // otherwise fall back to `levels * 3m`,
                    // or a static default of 10m
                    'fill-extrusion-height': [
                        'coalesce',
                        ['*', ['get', 'render_height'], 1],
                        10
                    ],
                    // use the feature’s `min_height` if present
                    'fill-extrusion-base': ['coalesce', ['get', 'min_height'], 0],
                    'fill-extrusion-opacity': 0.6
                }
            });
        });
    });
</script>

<div id="map" class="relative grow"></div>
