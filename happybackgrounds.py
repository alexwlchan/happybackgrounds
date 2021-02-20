#!/usr/bin/env python

import colorsys
import os
import random
from urllib.request import urlretrieve
from xml.etree import ElementTree as ET
import zipfile


# See https://fontawesome.com/how-to-use/on-the-desktop/setup/getting-started
FA_VERSION = "5.15.2"
FA_URL = f"https://use.fontawesome.com/releases/v{FA_VERSION}/fontawesome-free-{FA_VERSION}-desktop.zip"

# Where the Font Awesome icons will be saved.  If this is a persistent
# directory, then it will be saved between different runs of the script.
FA_LOCAL_PATH = os.path.basename(FA_URL)


def get_font_awesome_icon_path(*, icon_name):
    """
    Returns the <path> element of a Font Awesome icon.
    """
    if not os.path.exists(FA_LOCAL_PATH):
        urlretrieve(url=FA_URL, filename=FA_LOCAL_PATH)

    with zipfile.ZipFile(FA_LOCAL_PATH) as zf:
        # The names in this archive are something like:
        #
        #     fontawesome-free-5.15.2-desktop/svgs/solid/snowflake.svg
        #
        # I've picked the solid icons for now.  I'm not sure what the
        # difference between "solid" and "regular" is, and I'm assuming
        # @happyautomata doesn't want "brands".
        inner_name = f"fontawesome-free-{FA_VERSION}-desktop/svgs/solid/{icon_name}.svg"
        icon_contents = zf.read(inner_name)

        # The contents of a Font Awesome SVG goes something like:
        #
        #   <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512">
        #       <!-- Font Awesome Free 5.15.2 by @fontawesome … -->
        #       <path d="…"/>
        #   </svg>
        #
        # The Python XML parser ignores comments; this gets added separately.
        # We care about getting the <path> element which defines the icon.
        root = ET.fromstring(icon_contents)

        for element in root:
            if element.tag == "{http://www.w3.org/2000/svg}path":
                return ET.tostring(element).decode("ascii")
        else:  # no return
            raise RuntimeError(f"Could not find <path> in {inner_name}!")


def create_svg(
    *, background, icon_name, min_icon_count, max_icon_count, min_scale, max_scale
):
    """
    Creates an SVG file.  Returns the path to the generated SVG.

    :param background: A background colour as a six-char CSS colour
        (e.g. #ff0000).
    :param icon_name: The name of the Font Awesome icon to use
        (e.g. snowflake)
    """
    width = 1600
    height = 900

    # We want an SVG with a 16:9 ratio and the specified background color.
    lines = [
        f'<svg viewBox="0 0 {width} {height}" style="background-color:{background}" xmlns="http://www.w3.org/2000/svg">',
        f"""
        <!--
            Font Awesome Free {FA_VERSION} by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free
            (Icons: CC BY 4.0, Fonts: SIL OFL 1.1, Code: MIT License)
        -->
        """,
    ]

    # Parse the CSS colour.  We're only going to vary the lightness of the
    # generated icons, so work out what we're varying it between -- i.e. are
    # we going darker than the background, or lighter?
    red = int(background[1:3], 16) / 255
    green = int(background[3:5], 16) / 255
    blue = int(background[5:7], 16) / 255

    hue, lightness, saturation = colorsys.rgb_to_hls(red, green, blue)

    # Light background => darken
    # Dark background => lighten
    # Middling => choose at random
    #
    # 0.2 is chosen at random
    is_light_bg = lightness > 0.8
    is_dark_bg = lightness < 0.2

    darken_icons = is_light_bg or (not is_dark_bg and random.random() > 0.5)

    if darken_icons:
        min_lightness, max_lightness = (max(0, lightness - 0.2), lightness)
    else:
        min_lightness, max_lightness = (lightness, min(lightness + 0.2, 1))

    # Get the icon path, and render it at various points on the background.
    icon_count = random.randint(min_icon_count, max_icon_count)
    icon_path = get_font_awesome_icon_path(icon_name=icon_name)

    for _ in range(icon_count):
        x_start = random.randint(-100, width + 100)
        y_start = random.randint(-100, height + 100)
        rotation_angle = random.randint(0, 360)
        scale = random.uniform(min_scale, max_scale)

        icon_lightness = random.uniform(min_lightness, max_lightness)
        r, g, b = colorsys.hls_to_rgb(hue, icon_lightness, saturation)
        r, g, b = (int(r * 255), int(g * 255), int(b * 255))
        fill_color = f"#{r:02x}{g:02x}{b:02x}"

        lines.append(
            f"""
        <g transform="translate({x_start} {y_start}) scale({scale} {scale})"
           style="fill: {fill_color}">
            <g transform="rotate({rotation_angle} 0 0)">
                {icon_path}
            </g>
        </g>"""
        )

    # Add the closing tags, write to the file.
    lines.append("</svg>")

    with open("output.svg", "w") as outfile:
        outfile.write("\n".join(lines))
    return "output.svg"


if __name__ == "__main__":
    create_svg(
        background="#d6fcff",
        icon_name="snowflake",
        min_icon_count=5,
        max_icon_count=10,
        min_scale=0.2,
        max_scale=1,
    )
