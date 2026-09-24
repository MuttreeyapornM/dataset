import os
import subprocess
import shutil

# โฟลเดอร์ที่เก็บ .json
json_folder = "label/SHADOW_label"
output_folder = "label/SHADOW_masks"
os.makedirs(output_folder, exist_ok=True)

# ลูปแปลงทุก .json
for filename in os.listdir(json_folder):
    if filename.endswith(".json"):
        base = os.path.splitext(filename)[0]
        json_path = os.path.join(json_folder, filename)
        temp_output = os.path.join(json_folder, base + "_json")

        print(f"🛠 แปลง: {filename}")
        subprocess.run([
            "python", "-m", "labelme.cli.json_to_dataset", json_path
        ])

        label_path = os.path.join(temp_output, "label.png")
        if os.path.exists(label_path):
            shutil.move(label_path, os.path.join(output_folder, f"{base}.png"))
            print(f"✅ ได้: {base}.png")
        else:
            print(f"❌ ไม่พบ label.png จาก {filename}")

print("\n✅ เสร็จสิ้น: ทุกไฟล์ .json ถูกแปลงและรวมไว้ในโฟลเดอร์", output_folder)
