import json
import numpy as np
import cv2
import os

# ขั้นตอนนี้ใช้สำหรับดูภาพที่ label แล้วเท่านั้น
# อ่าน JSON จาก label/ จับคู่รูปจาก original/ แล้วบันทึกภาพ overlay ลง label_preview/
original_root = "original"
json_root = "label"
preview_output_folder = "label_preview"
alpha = 0.45

# ถ้าต้องการแปลงเฉพาะชุดเดียว ให้ใส่ชื่อ folder เช่น "WET_label"
# ถ้าต้องการทุกชุด ให้ใช้ None
target_label_folder = None

# กำหนดการจับคู่ชื่อคลาสกับ ID และสีที่แสดงใน label image
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
    "blackground": 999
}

# กำหนดสีที่ใช้สำหรับแต่ละ class (สี RGB)
id_to_color = {
    0: [0, 255, 0],      # green for drivable Area (RGB)
    1: [255, 0, 0],      # red for traffic cone (RGB)
    2: [128, 0, 128],    # purple for car (RGB)
    3: [0, 0, 255],      # blue for person (RGB)
    4: [192, 192, 192],  # gray for slidewalk (RGB)
    5: [0, 255, 255],    # cyan for parking (RGB)
    6: [255, 0, 255],    # magenta for crosswalk (RGB)
    7: [0, 128, 0],      # dark green for vegetation (RGB)
    8: [0, 0, 0],         # black for golf cart (RGB)
    999: [255, 255, 255]  # white for background preview (RGB)
}

image_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}


def build_image_index(root_folder):
    image_index = {}
    for current_root, _, files in os.walk(root_folder):
        for filename in files:
            name, ext = os.path.splitext(filename)
            if ext.lower() in image_extensions:
                image_path = os.path.join(current_root, filename)
                image_index.setdefault(name, []).append(image_path)
    return image_index


def find_original_image(json_path, image_index):
    base_name = os.path.splitext(os.path.basename(json_path))[0]
    candidates = image_index.get(base_name, [])
    if not candidates:
        return None

    label_group = os.path.basename(os.path.dirname(json_path))
    label_group = label_group.replace("_label", "").lower()
    matched = [
        path for path in candidates
        if label_group in os.path.basename(os.path.dirname(path)).replace("ori", "").lower()
    ]
    return sorted(matched or candidates)[0]


def draw_shape(label_img, shape, bgr_color):
    points = np.array(shape.get("points", []), dtype=np.int32)
    if len(points) < 2:
        return

    shape_type = shape.get("shape_type", "polygon")
    if shape_type == "rectangle":
        cv2.rectangle(label_img, tuple(points[0]), tuple(points[1]), bgr_color, thickness=-1)
    elif shape_type == "circle":
        center, edge = points[0], points[1]
        radius = ((edge[0] - center[0]) ** 2 + (edge[1] - center[1]) ** 2) ** 0.5
        cv2.circle(label_img, tuple(center), int(radius), bgr_color, thickness=-1)
    else:
        cv2.fillPoly(label_img, [points], bgr_color)


# ฟังก์ชันแปลง JSON เป็นภาพ overlay สำหรับดู label บนภาพจริง
def create_label_preview(json_path, image_path, output_folder):
    with open(json_path, "r", encoding="utf-8") as f:
        label_data = json.load(f)

    original_img = cv2.imread(image_path)
    if original_img is None:
        print(f"❌ อ่านภาพ original ไม่ได้: {image_path}")
        return

    height, width = original_img.shape[:2]
    label_img = np.zeros((height, width, 3), dtype=np.uint8)
    label_area = np.zeros((height, width), dtype=np.uint8)

    # วาดแต่ละ shape ลงใน label image
    unknown_labels = set()
    for shape in label_data.get("shapes", []):
        class_name = shape["label"]
        class_id = class_to_id.get(class_name)

        if class_id is not None:
            color = id_to_color.get(class_id, [0, 0, 0])  # กำหนดสีตาม ID

            # แปลงสีจาก RGB เป็น BGR สำหรับ OpenCV
            bgr_color = [color[2], color[1], color[0]]  # แปลง RGB เป็น BGR
            draw_shape(label_img, shape, bgr_color)
            draw_shape(label_area, shape, 255)
        else:
            unknown_labels.add(class_name)

    mask_area = label_area > 0
    overlay = original_img.copy()
    overlay[mask_area] = cv2.addWeighted(
        original_img[mask_area],
        1 - alpha,
        label_img[mask_area],
        alpha,
        0,
    )

    # สร้างชื่อไฟล์ output
    base_name = os.path.splitext(os.path.basename(json_path))[0]
    group_name = os.path.basename(os.path.dirname(json_path))
    group_output_folder = os.path.join(output_folder, group_name)
    os.makedirs(group_output_folder, exist_ok=True)

    preview_output_path = os.path.join(group_output_folder, f"{base_name}_preview.png")
    cv2.imwrite(preview_output_path, overlay)

    if unknown_labels:
        print(f"⚠️  พบ class ที่ยังไม่อยู่ใน class_to_id ใน {json_path}: {sorted(unknown_labels)}")
    print(f"✅ บันทึกภาพ preview: {preview_output_path}")


def iter_json_files(root_folder):
    if target_label_folder:
        search_root = os.path.join(root_folder, target_label_folder)
    else:
        search_root = root_folder

    for current_root, _, files in os.walk(search_root):
        for filename in sorted(files):
            if filename.endswith(".json"):
                yield os.path.join(current_root, filename)


os.makedirs(preview_output_folder, exist_ok=True)
image_index = build_image_index(original_root)

converted_count = 0
missing_image_count = 0

for json_path in iter_json_files(json_root):
    image_path = find_original_image(json_path, image_index)
    if image_path is None:
        missing_image_count += 1
        print(f"❌ ไม่พบภาพ original สำหรับ: {json_path}")
        continue

    create_label_preview(json_path, image_path, preview_output_folder)
    converted_count += 1

print(f"\n🎉 เสร็จสิ้น: สร้าง preview แล้ว {converted_count} ไฟล์")
if missing_image_count:
    print(f"⚠️  มี JSON ที่หา original ไม่เจอ {missing_image_count} ไฟล์")
