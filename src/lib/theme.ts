
export function getCarbonTheme(mode: "light" | "dark" | undefined) {

    switch (mode) {
        case "light":
            return "white"
        case "dark":
            return "g100"
        default:
            return "white"
    }

}