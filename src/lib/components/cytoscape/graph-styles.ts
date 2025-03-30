import type {StylesheetStyle} from "cytoscape";
import {getTextColor} from "$lib/theme.ts";

export type StyleEntry = {
    [parent: string]: string;
};

export async function getStyleData(styleUrl: string): Promise<StyleEntry[]> {
    const response = await fetch(styleUrl);
    return await response.json();
}

export async function getStyles(styleData: StyleEntry[], mode: "light" | "dark" | undefined, showCode: boolean): Promise<StylesheetStyle[]> {

    let defaultStyles: StylesheetStyle[] = [
        {
            selector: 'node',
            style: {
                'label': showCode ? 'data(id)': 'data(title)',
                'text-valign': 'center',
                'text-halign': 'center',
                'background-color': '#757575',
                'text-wrap': 'wrap',
                'text-max-width': '200', // i have no clue what the unit is, maybe px
                'text-margin-y': 5,
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