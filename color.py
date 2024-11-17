import random

def generate_random_hex_colors(num):
    colors = []

    def is_contrasting(color):
        """Ensure the color is visible on a white background by checking luminance."""
        # Extract RGB components from the hex color
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)

        # Calculate luminance using the formula for brightness
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

        # Return True if the luminance is within a good range (50 to 200 is reasonable)
        return 50 <= luminance <= 200

    while len(colors) < num:
        # Generate a random 6-digit hex color
        random_color = "#{:06x}".format(random.randint(0, 0xFFFFFF))

        # Ensure the color has good contrast against a white background
        if is_contrasting(random_color):
            colors.append(random_color)

    return colors
