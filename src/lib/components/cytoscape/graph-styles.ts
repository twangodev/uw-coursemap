import type {StylesheetStyle} from "cytoscape";
import {getTextColor} from "$lib/theme.ts";

type StyleData = {
    [parent: string]: string;
};

export async function getStyles(styleUrl: string, mode: "light" | "dark" | undefined): Promise<StylesheetStyle[]> {

    let defaultStyles: StylesheetStyle[] = [
        {
            selector: 'node',
            style: {
                'label': 'data(id)',
                'text-valign': 'center',
                'text-halign': 'center',
                'background-color': '#757575',
                'color': getTextColor(mode)
            }
        },
        {
            selector: '.highlighted-nodes',
            style: {
                'border-width': 1,
                'border-color': getTextColor(mode),
                'border-style': 'solid',
            }
        },
        {
            selector: '.faded',
            style: {
                'opacity': 0.25,
                'text-opacity': 0.25,
            }
        },
        {
            selector: '*',
            style: {
                'transition-property': 'opacity',
                'transition-duration': 0.2,
            }
        },
        {
            selector: 'node[type="compound"]',
            style: {
                'text-valign': 'top',
                'border-width': 0,
                'background-opacity': 0,
                label: '',
            }
        },
        {
            selector: 'edge',
            style: {
                'width': 1,
                'line-color': getTextColor(mode),
                'curve-style': 'straight',
                'target-arrow-color': getTextColor(mode),
                'target-arrow-shape': 'triangle',
                'source-distance-from-node': 5,
                'target-distance-from-node': 5,
                'text-wrap': 'wrap',
                'font-size': 10,
            }
        },
        {
            selector: '.highlighted-edges',
            style: {
                'width': 2,
            }
        },
        {
            selector: '.no-overlay',
            style: {
                'overlay-padding': 0,
                'overlay-opacity': 0,
            }
        }
    ]

    let styleResponse = await fetch(styleUrl);
    let styleData: StyleData[] = await styleResponse.json();

    const styles = styleData.map(item => {
        const [parent, color] = Object.entries(item)[0];
        return {
            selector: `node[parent="${parent}"]`,
            style: {
                'background-color': color,
            },
        };
    });


    return defaultStyles.concat(styles);
}