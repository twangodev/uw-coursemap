import random
import colorsys


def generate_accessible_color():
    """
    Generate an accessible random hex color that meets WCAG contrast ratios for both
    black and white text. The function uses Material 3's tonal idea by adjusting the
    lightness value via binary search, targeting a mid-tone that typically yields
    sufficient contrast. Additionally, the saturation is restricted to avoid near-gray colors.

    Returns:
        str: A hex color string in the form "#RRGGBB".
    """
    def relative_luminance(r, g, b):
        # Convert sRGB to linear light values
        def to_linear(c):
            return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
        R_lin = to_linear(r)
        G_lin = to_linear(g)
        B_lin = to_linear(b)
        return 0.2126 * R_lin + 0.7152 * G_lin + 0.0722 * B_lin

    # Choose a random hue in [0, 1)
    h = random.random()
    # Restrict saturation to avoid near-gray colors; pick from [0.5, 1.0] for vibrant colors.
    s = random.uniform(0.5, 1.0)

    # Use binary search to find a suitable lightness value that provides good contrast.
    # We aim for a relative luminance of about 0.18.
    low, high = 0.0, 1.0
    chosen_l = 0.5  # Start in the middle

    for _ in range(20):
        r, g, b = colorsys.hls_to_rgb(h, chosen_l, s)
        lum = relative_luminance(r, g, b)
        # Adjust lightness based on whether the luminance is too high or too low.
        if lum > 0.18:
            high = chosen_l
        else:
            low = chosen_l
        chosen_l = (low + high) / 2.0

    # Convert final HLS value to RGB and then to HEX.
    r, g, b = colorsys.hls_to_rgb(h, chosen_l, s)
    R = int(round(r * 255))
    G = int(round(g * 255))
    B = int(round(b * 255))
    return f"#{R:02x}{G:02x}{B:02x}"

def generate_random_hex_colors(parents, color_map):
    """
    For each parent identifier in the given set, either retrieve its existing color
    from color_map or generate a new accessible hex color using generate_accessible_color().
    The colors are consistent: once a parent is assigned a color, it is reused.

    Args:
        parents (set of str): Set of parent identifiers.
        color_map (dict): Mapping from a parent identifier to a hex color string.

    Returns:
        list: A list of hex color strings corresponding to the parents.
    """
    colors = []
    for parent in parents:
        if parent in color_map:
            colors.append(color_map[parent])
        else:
            new_color = generate_accessible_color()
            color_map[parent] = new_color
            colors.append(new_color)
    return colors