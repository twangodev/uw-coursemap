
export function getCarbonTheme(mode: "light" | "dark" | undefined) {

    switch (mode) {
        case "light":
            return "white"
        case "dark":
            return "g90"
        default:
            return "white"
    }

}