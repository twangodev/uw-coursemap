import type {SlideParams} from "svelte/transition";
import {quadInOut} from "svelte/easing";

export const slideIn: SlideParams = {
    duration: 500,
    delay: 0,
    easing:quadInOut
}
