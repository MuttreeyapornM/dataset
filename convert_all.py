import os
import subprocess
import shutil

# โฟลเดอร์ที่เก็บไฟล์ .json
json_folder = "labelme_jsons"
img_output_folder = "converted_all/_img"
label_output_folder = "converted_all/_label"
os.makedirs(img_output_folder, exist_ok=True)
os.makedirs(label_output_folder, exist_ok=True)

# ลูปแปลงทุกไฟล์ .json
for filename in os.listdir(json_folder):
    if filename.endswith(".json"):
        base = os.path.splitext(filename)[0]
        json_path = os.path.join(json_folder, filename)
        temp_output = os.path.join(json_folder, base + "_json")

        print(f"🛠 กำลังแปลง: {filename}")
        subprocess.run([
            "python", "-m", "labelme.cli.json_to_dataset", json_path
        ])

        # แยกเก็บ img กับ label
        img_path = os.path.join(temp_output, "img.png")
        label_path = os.path.join(temp_output, "label.png")

        if os.path.exists(img_path):
            shutil.move(img_path, os.path.join(img_output_folder, f"{base}_img.png"))
            print(f"✅ บันทึกภาพ: {base}_img.png")
        else:
            print(f"❌ ไม่พบ img.png จาก {filename}")

        if os.path.exists(label_path):
            shutil.move(label_path, os.path.join(label_output_folder, f"{base}_label.png"))
            print(f"✅ บันทึก label: {base}_label.png")
        else:
            print(f"❌ ไม่พบ label.png จาก {filename}")

        # ลบโฟลเดอร์ชั่วคราว
        shutil.rmtree(temp_output, ignore_errors=True)

print("\n🎉 เสร็จสิ้น: แยกไฟล์ภาพและ label ไว้ที่ _img และ _label ในโฟลเดอร์ converted_all")
