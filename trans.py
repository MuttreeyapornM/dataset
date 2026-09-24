import json
import os
import struct
import zlib


json_folder = "label/WET_label"
output_folder = "label/WET_masks"
preview_output_folder = "label/WET_masks_preview"

# Keep this mapping the same as overlay.py so generated masks use the same IDs.
class_to_id = {
    "drivable Area": 0,
    "drivable area": 0,
    "traffic cone": 1,
    "car": 2,
    "person": 3,
    "slidewalk": 4,
    "parking": 5,
    "crosswalk": 6,
    "vegetation": 7,
    "golf cart": 8,
    "background": 999,
    "blackground": 999,
}

background_id = 999

id_to_color = {
    0: [0, 255, 0],      # green for drivable Area (RGB)
    1: [255, 0, 0],      # red for traffic cone (RGB)
    2: [128, 0, 128],    # purple for car (RGB)
    3: [0, 0, 255],      # blue for person (RGB)
    4: [192, 192, 192],  # gray for slidewalk (RGB)
    5: [0, 255, 255],    # cyan for parking (RGB)
    6: [255, 0, 255],    # magenta for crosswalk (RGB)
    7: [0, 128, 0],      # dark green for vegetation (RGB)
    8: [0, 0, 0],        # black for golf cart (RGB)
    999: [255, 255, 255],
}


def write_png_u16_grayscale(path, width, height, pixels):
    def chunk(chunk_type, data):
        payload = chunk_type + data
        checksum = zlib.crc32(payload) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + payload + struct.pack(">I", checksum)

    raw = bytearray()
    for y in range(height):
        raw.append(0)
        row_start = y * width
        for x in range(width):
            raw.extend(struct.pack(">H", pixels[row_start + x]))

    png = bytearray()
    png.extend(b"\x89PNG\r\n\x1a\n")
    png.extend(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 16, 0, 0, 0, 0)))
    png.extend(chunk(b"IDAT", zlib.compress(bytes(raw))))
    png.extend(chunk(b"IEND", b""))

    with open(path, "wb") as f:
        f.write(png)


def write_png_rgb(path, width, height, pixels):
    def chunk(chunk_type, data):
        payload = chunk_type + data
        checksum = zlib.crc32(payload) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + payload + struct.pack(">I", checksum)

    raw = bytearray()
    for y in range(height):
        raw.append(0)
        row_start = y * width
        for x in range(width):
            raw.extend(id_to_color.get(pixels[row_start + x], [0, 0, 0]))

    png = bytearray()
    png.extend(b"\x89PNG\r\n\x1a\n")
    png.extend(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)))
    png.extend(chunk(b"IDAT", zlib.compress(bytes(raw))))
    png.extend(chunk(b"IEND", b""))

    with open(path, "wb") as f:
        f.write(png)


def fill_span(mask, width, height, y, x1, x2, value):
    if y < 0 or y >= height:
        return

    start = max(0, min(x1, x2))
    end = min(width - 1, max(x1, x2))
    offset = y * width
    for x in range(start, end + 1):
        mask[offset + x] = value


def fill_rectangle(mask, width, height, p1, p2, value):
    x1, y1 = p1
    x2, y2 = p2
    for y in range(max(0, min(y1, y2)), min(height - 1, max(y1, y2)) + 1):
        fill_span(mask, width, height, y, x1, x2, value)


def fill_circle(mask, width, height, center, edge, value):
    cx, cy = center
    ex, ey = edge
    radius = int(((ex - cx) ** 2 + (ey - cy) ** 2) ** 0.5)
    radius_sq = radius * radius

    for y in range(max(0, cy - radius), min(height - 1, cy + radius) + 1):
        dy = y - cy
        dx = int((radius_sq - dy * dy) ** 0.5)
        fill_span(mask, width, height, y, cx - dx, cx + dx, value)


def fill_polygon(mask, width, height, points, value):
    if len(points) < 3:
        return

    min_y = max(0, min(y for _, y in points))
    max_y = min(height - 1, max(y for _, y in points))
    edges = list(zip(points, points[1:] + points[:1]))

    for y in range(min_y, max_y + 1):
        scan_y = y + 0.5
        intersections = []
        for (x1, y1), (x2, y2) in edges:
            if y1 == y2:
                continue
            if min(y1, y2) <= scan_y < max(y1, y2):
                x = x1 + (scan_y - y1) * (x2 - x1) / (y2 - y1)
                intersections.append(int(x))

        intersections.sort()
        for i in range(0, len(intersections) - 1, 2):
            fill_span(mask, width, height, y, intersections[i], intersections[i + 1], value)


def draw_shape(mask, shape, class_id):
    points = [(int(x), int(y)) for x, y in shape.get("points", [])]
    if len(points) < 2:
        return

    shape_type = shape.get("shape_type", "polygon")
    if shape_type == "rectangle":
        fill_rectangle(mask, mask.width, mask.height, points[0], points[1], int(class_id))
    elif shape_type == "circle":
        fill_circle(mask, mask.width, mask.height, points[0], points[1], int(class_id))
    else:
        fill_polygon(mask, mask.width, mask.height, points, int(class_id))


class Mask(list):
    def __init__(self, width, height, fill_value):
        super().__init__([fill_value] * (width * height))
        self.width = width
        self.height = height


def create_mask(json_path, output_path, preview_path=None):
    with open(json_path, "r", encoding="utf-8") as f:
        label_data = json.load(f)

    height = label_data.get("imageHeight")
    width = label_data.get("imageWidth")
    if not height or not width:
        raise ValueError(f"Missing imageHeight/imageWidth in {json_path}")

    width = int(width)
    height = int(height)
    mask = Mask(width, height, background_id)
    unknown_labels = set()

    for shape in label_data.get("shapes", []):
        class_name = shape.get("label")
        class_id = class_to_id.get(class_name)
        if class_id is None:
            unknown_labels.add(class_name)
            continue

        draw_shape(mask, shape, class_id)

    write_png_u16_grayscale(output_path, width, height, mask)
    if preview_path:
        write_png_rgb(preview_path, width, height, mask)

    return unknown_labels


def main():
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(preview_output_folder, exist_ok=True)

    converted_count = 0
    unknown_by_file = {}

    for filename in sorted(os.listdir(json_folder)):
        if not filename.endswith(".json"):
            continue

        base = os.path.splitext(filename)[0]
        json_path = os.path.join(json_folder, filename)
        output_path = os.path.join(output_folder, f"{base}.png")
        preview_path = os.path.join(preview_output_folder, f"{base}_preview.png")

        print(f"Converting: {filename}")
        unknown_labels = create_mask(json_path, output_path, preview_path)
        converted_count += 1

        if unknown_labels:
            unknown_by_file[filename] = sorted(unknown_labels)
            print(f"Unknown labels in {filename}: {sorted(unknown_labels)}")
        else:
            print(f"Saved: {output_path}")
            print(f"Saved preview: {preview_path}")

    print(f"\nDone: converted {converted_count} JSON files into {output_folder}")
    print(f"Preview images were saved into {preview_output_folder}")
    if unknown_by_file:
        print("Some labels were skipped because they are not in class_to_id:")
        for filename, labels in unknown_by_file.items():
            print(f"- {filename}: {labels}")


if __name__ == "__main__":
    main()
