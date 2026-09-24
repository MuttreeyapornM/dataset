import base64
import json
import os
import shutil

from trans import create_mask


json_folder = "labelme_jsons"
img_output_folder = "converted_all/_img"
label_output_folder = "converted_all/_label"
preview_output_folder = "converted_all/_label_preview"

os.makedirs(img_output_folder, exist_ok=True)
os.makedirs(label_output_folder, exist_ok=True)
os.makedirs(preview_output_folder, exist_ok=True)


def save_image_from_labelme_json(label_data, json_path, output_path):
    image_data = label_data.get("imageData")
    if image_data:
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(image_data))
        return True

    image_path = label_data.get("imagePath")
    if not image_path:
        return False

    source_path = image_path
    if not os.path.isabs(source_path):
        source_path = os.path.join(os.path.dirname(json_path), source_path)

    if not os.path.exists(source_path):
        return False

    shutil.copy2(source_path, output_path)
    return True


def main():
    converted_count = 0
    missing_image_count = 0
    unknown_by_file = {}

    for filename in sorted(os.listdir(json_folder)):
        if not filename.endswith(".json"):
            continue

        base = os.path.splitext(filename)[0]
        json_path = os.path.join(json_folder, filename)
        img_output_path = os.path.join(img_output_folder, f"{base}_img.png")
        label_output_path = os.path.join(label_output_folder, f"{base}_label.png")
        preview_output_path = os.path.join(preview_output_folder, f"{base}_label_preview.png")

        print(f"Converting: {filename}")
        with open(json_path, "r", encoding="utf-8") as f:
            label_data = json.load(f)

        if save_image_from_labelme_json(label_data, json_path, img_output_path):
            print(f"Saved image: {img_output_path}")
        else:
            missing_image_count += 1
            print(f"Missing image data/source for {filename}")

        unknown_labels = create_mask(json_path, label_output_path, preview_output_path)
        converted_count += 1

        if unknown_labels:
            unknown_by_file[filename] = sorted(unknown_labels)
            print(f"Unknown labels in {filename}: {sorted(unknown_labels)}")
        else:
            print(f"Saved label: {label_output_path}")
            print(f"Saved preview: {preview_output_path}")

    print(f"\nDone: converted {converted_count} JSON files into converted_all")
    print(f"Images: {img_output_folder}")
    print(f"ID masks: {label_output_folder}")
    print(f"Preview masks: {preview_output_folder}")

    if missing_image_count:
        print(f"Files with missing image data/source: {missing_image_count}")

    if unknown_by_file:
        print("Some labels were skipped because they are not in class_to_id:")
        for filename, labels in unknown_by_file.items():
            print(f"- {filename}: {labels}")


if __name__ == "__main__":
    main()
