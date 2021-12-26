def write_poly_to_svg(svg_path, polygons, bbox_a, bbox_b, units):
    with open(svg_path, "w") as svg_file:
        # Write header
        width = abs(bbox_a[0] - bbox_b[0])
        height = abs(bbox_a[1] - bbox_b[1])

        svg_file.writelines(
            [
                '<?xml version="1.0" standalone="no"?>\n',
                '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" \n',
                '  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n',
                f'<svg width="{width}{units}" height="{height}{units}" ',
                f'viewBox="{0} {0} {width} {height}"\n',
                '     xmlns="http://www.w3.org/2000/svg" version="1.1">\n',
                "<desc>Outline to SVG export</desc>\n",
            ]
        )

        # Write polyline
        for poly in polygons:
            poly_str = poly.svg()
            # Remove stroke
            poly_str = poly_str.replace("stroke-width=\"2.0\"",  "stroke-width=\"0\"")
            # Max Opacity
            poly_str = poly_str.replace("opacity=\"0.6\"", "opacity=\"1\"")
            # Color Black
            poly_str = poly_str.replace("fill=\"#66cc99\"", "fill=\"#000000\"")

            # Write line
            svg_file.write("".join(["\t", poly_str, "\n"]))

        # Write footer
        svg_file.write(r"</svg>")
