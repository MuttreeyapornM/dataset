import os
import shutil
import random

# กำหนดโฟลเดอร์ต้นฉบับ
image_folder = 'images'
label_folder = 'labels'

# โฟลเดอร์ปลายทาง
train_image_folder = 'train/images'
train_label_folder = 'train/labels'

val_image_folder = 'val/images'
val_label_folder = 'val/labels'

test_image_folder = 'test/images'
test_label_folder = 'test/labels'

# สร้างโฟลเดอร์ที่ต้องการ
for folder in [train_image_folder, train_label_folder, val_image_folder, val_label_folder, test_image_folder, test_label_folder]:
    os.makedirs(folder, exist_ok=True)

# ดึงไฟล์ภาพทั้งหมด
image_files = [f for f in os.listdir(image_folder) if f.endswith('.png')]

# สุ่มจัดกลุ่มข้อมูล
random.shuffle(image_files)

# แบ่งข้อมูล
train_images = image_files[:int(0.7 * len(image_files))]
val_images = image_files[int(0.7 * len(image_files)):int(0.85 * len(image_files))]
test_images = image_files[int(0.85 * len(image_files)):]

# ฟังก์ชันจับคู่ชื่อ label จากชื่อ image
def get_label_filename(image_filename):
    return image_filename.replace('_img.png', '_label.png')

# คัดลอกไฟล์
for img in train_images:
    shutil.copy(os.path.join(image_folder, img), os.path.join(train_image_folder, img))
    label = get_label_filename(img)
    shutil.copy(os.path.join(label_folder, label), os.path.join(train_label_folder, label))

for img in val_images:
    shutil.copy(os.path.join(image_folder, img), os.path.join(val_image_folder, img))
    label = get_label_filename(img)
    shutil.copy(os.path.join(label_folder, label), os.path.join(val_label_folder, label))

for img in test_images:
    shutil.copy(os.path.join(image_folder, img), os.path.join(test_image_folder, img))
    label = get_label_filename(img)
    shutil.copy(os.path.join(label_folder, label), os.path.join(test_label_folder, label))

print("🎉 แบ่งข้อมูลเสร็จสมบูรณ์แล้ว!")
