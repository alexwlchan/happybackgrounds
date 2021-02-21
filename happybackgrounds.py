#!/usr/bin/env python

import argparse
import colorsys
import os
import random
import sys
import tempfile
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
    Returns the (width, height, <path> element) of a Font Awesome icon.
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

        _, _, width, height = root.attrib["viewBox"].split()

        for element in root:
            if element.tag == "{http://www.w3.org/2000/svg}path":
                return (int(width), int(height), ET.tostring(element).decode("ascii"))
        else:  # no return
            raise RuntimeError(f"Could not find <path> in {inner_name}!")


def create_xy_positions(
    *, width, height, columns, rows, min_nudge, max_nudge, count, avoid_center
):
    """
    Based on an algorithm from Kate's friend.

    This will give you the (x, y) coordinates for the top left-hand corner
    of the icon.
    """
    # Put the icons randomly on an N×M grid
    valid_positions = [(x, y) for x in range(columns) for y in range(rows)]
    random.shuffle(valid_positions)

    if avoid_center:
        valid_positions = [
            (x, y)
            for (x, y) in valid_positions
            if (x <= columns / 4 or x >= 3 * columns / 4)
            and (y <= rows / 4 or y >= 3 * rows / 4)
        ]

    # Choose a direction and amount to nudge them by
    nudge = random.uniform(min_nudge, max_nudge)
    for x, y in valid_positions[:count]:
        # x = x + ((1 - random.random() * 2) * nudge)
        # y = y + ((1 - random.random() * 2) * nudge)

        # How does this map to our canvas?
        row_height = height / rows
        column_width = width / columns

        yield (x * column_width, y * row_height)


def create_fill_colors(*, background_color):
    """
    Given the hex string of the background colour (e.g. #ff0000), generate
    the hex strings of other, similar colours.
    """
    # Parse the CSS colour.  We're only going to vary the lightness of the
    # generated icons, so work out what we're varying it between -- i.e. are
    # we going darker than the background, or lighter?
    red = int(background_color[1:3], 16) / 255
    green = int(background_color[3:5], 16) / 255
    blue = int(background_color[5:7], 16) / 255

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

    while True:
        icon_lightness = random.uniform(min_lightness, max_lightness)
        r, g, b = colorsys.hls_to_rgb(hue, icon_lightness, saturation)
        r, g, b = (int(r * 255), int(g * 255), int(b * 255))
        yield f"#{r:02x}{g:02x}{b:02x}"


def create_svg(
    *,
    background,
    icon_name,
    min_icon_count,
    max_icon_count,
    min_scale,
    max_scale,
    avoid_center=False,
    out_path=None,
):
    """
    Creates an SVG file.  Returns the path to the generated SVG.

    :param background: A background colour as a six-char CSS colour
        (e.g. #ff0000).
    :param icon_name: The name of the Font Awesome icon to use
        (e.g. snowflake)
    :param min_icon_count: What's the smallest number of icons to add?
    :param max_icon_count: What's the most icons to add?
    :param min_scale: How small can the icons get?
    :param max_scale: How big can the icons get?
    :param out_path: Where to save the file.
    :param avoid_center: Should it avoid the centre?

    Note: because of the way icons are added, the min/max icon counts
    are rough estimates, and you may see fewer icons in the viewbox than
    you actually asked for.

    """
    width = 1600
    height = 900

    # We want an SVG with a 16:9 ratio and the specified background color.
    # I'm including a <rect> so that ImageMagick picks up the background.
    lines = [
        f'<svg viewBox="0 0 {width} {height}" style="background-color:{background}" xmlns="http://www.w3.org/2000/svg">',
        f"""
        <!--
            Font Awesome Free {FA_VERSION} by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free
            (Icons: CC BY 4.0, Fonts: SIL OFL 1.1, Code: MIT License)
        -->
        <rect style="fill:{background}" x="0" y="0" width="{width}" height="{height}"/>
        """,
    ]

    # Get the icon path, and render it at various points on the background.
    count = random.randint(min_icon_count, max_icon_count)
    icon_width, icon_height, icon_path = get_font_awesome_icon_path(icon_name=icon_name)

    for (x, y), fill_color in zip(
        create_xy_positions(
            width=width,
            height=height,
            columns=width // 100,
            rows=height // 100,
            min_nudge=-0.2,
            max_nudge=0.2,
            count=count,
            avoid_center=avoid_center,
        ),
        create_fill_colors(background_color=background)
    ):
        scale = random.uniform(min_scale, max_scale)

        rotation_angle = random.randint(0, 360)
        rotation_center_x = scale * icon_width // 2
        rotation_center_y = scale * icon_height // 2

        # icon_blur = random.randint(0, 20)
        icon_blur = 0

        lines.append(
            f"""
        <defs>
            <filter id="blur{icon_blur}" x="0" y="0">
                <feGaussianBlur in="SourceGraphic" stdDeviation="{icon_blur} {icon_blur}"/>
            </filter>
        </defs>
        <g transform="translate({x} {y})
                      rotate({rotation_angle} {rotation_center_x} {rotation_center_y})
                      scale({scale} {scale})"
           style="fill: {fill_color}; filter: url(#blur{icon_blur})">
            {icon_path}
        </g>"""
        )

    # Add the closing tags, write to the file.  We tidy up the XML a bit.
    lines.append("</svg>")

    if out_path is None:
        _, out_path = tempfile.mkstemp(suffix=".svg")

    with open(out_path, "w") as outfile:
        outfile.write("\n".join(lines))

    return out_path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create low-contrast backgrounds from Font Awesome icons.  Prints the path to a generated SVG file."
    )
    parser.add_argument(
        "--background", help="a six-digit CSS colour (e.g. #ff0000)", required=True
    )
    parser.add_argument(
        "--icon_name",
        help="the Font Awesome icon to use (e.g. snowflake)",
        required=True,
    )
    parser.add_argument("--min_icon_count", type=int, default=5, help="(default: 5)")
    parser.add_argument("--max_icon_count", type=int, default=30, help="(default: 30)")
    parser.add_argument("--min_scale", type=float, default=0.15, help="(default: 0.15)")
    parser.add_argument("--max_scale", type=float, default=0.3, help="(default: 0.3)")
    parser.add_argument("--avoid_center", action="store_true")

    # Make a consideration for British people ;-)
    parser.add_argument("--avoid_centre", action="store_true")

    parser.add_argument("--out_path", help="Where to save the SVG")

    result = parser.parse_args()

    if result.min_icon_count > result.max_icon_count:
        sys.exit(
            f"error: --min_icon_count={result.min_icon_count} should be less than or equal to --max_icon_count={result.max_icon_count}"
        )

    if result.min_scale > result.max_scale:
        sys.exit(
            f"error: --min_scale={result.min_scale} should be less than or equal to --max_scale={result.max_scale}"
        )

    result = {
        name: getattr(result, name) for name in dir(result) if not name.startswith("_")
    }

    if result["avoid_centre"]:
        result["avoid_center"] = result["avoid_centre"]
    del result["avoid_centre"]

    return result


if __name__ == "__main__":
    kwargs = parse_args()
    out_path = create_svg(**kwargs)
    print(out_path)
