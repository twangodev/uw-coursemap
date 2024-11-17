function generateRandomHexColors(num: number): string[] {
    const colors: string[] = [];

    // Function to calculate luminance and ensure good contrast
    const isContrasting = (color: string): boolean => {
        // Extract RGB components from the hex color
        const r = parseInt(color.slice(1, 3), 16);
        const g = parseInt(color.slice(3, 5), 16);
        const b = parseInt(color.slice(5, 7), 16);

        // Calculate luminance using the formula for brightness
        const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;

        // Return true if the luminance is within a good range for contrast
        return luminance >= 50 && luminance <= 200;
    };

    while (colors.length < num) {
        // Generate a random 6-digit hex color
        const randomColor = `#${Math.floor(Math.random() * 16777215).toString(16).padStart(6, '0')}`;

        // Ensure the color has good contrast against a white background
        if (isContrasting(randomColor)) {
            colors.push(randomColor);
        }
    }

    return colors;
}

// Example usage: Generate 5 random hex color codes
const colorCodes = generateRandomHexColors(5);
console.log(colorCodes);
