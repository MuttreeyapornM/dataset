# Custom Dataset Utilities

โปรเจกต์นี้เป็นชุดสคริปต์สำหรับจัดการรูปภาพและไฟล์ label จาก LabelMe เพื่อช่วยเตรียมข้อมูลสำหรับงาน semantic segmentation

โครงสร้างข้อมูลหลักที่ใช้ตอนนี้:

```text
original/           # ภาพต้นฉบับ แยกเป็นหลายชุด เช่น WETori, SHADOWori
label/              # ไฟล์ label จาก LabelMe เช่น WET_label, SHADOW_label
label_preview/      # ภาพ preview ที่วาด label ทับภาพจริง จาก overlay.py
datasets/           # dataset ที่ split แล้ว ถ้ามีการสร้างไว้
prediction/         # ผลลัพธ์ prediction
```

## การติดตั้ง Dependencies

สคริปต์ส่วนใหญ่ใช้ Python, OpenCV และ NumPy

```bash
pip install opencv-python numpy
```

ถ้าจะใช้ `trans.py` หรือ `convert_all.py` ต้องมี LabelMe ด้วย:

```bash
pip install labelme
```

ถ้าจะใช้ `custom_datasets.py` สำหรับ PyTorch training ต้องมี PyTorch, torchvision และ Pillow:

```bash
pip install torch torchvision pillow
```

ถ้าใช้ virtual environment ที่มีอยู่ในโปรเจกต์:

```bash
source myenv/bin/activate
```

## Workflow แนะนำ

### 1. ตรวจ label ด้วยภาพ preview

ใช้ [overlay.py](overlay.py) เพื่ออ่านไฟล์ `.json` จาก `label/`, จับคู่กับภาพต้นฉบับใน `original/`, แล้วสร้างภาพ overlay สำหรับตรวจว่า label ถูกต้องหรือไม่

```bash
python overlay.py
```

ผลลัพธ์:

```text
label_preview/SHADOW_label/merged_000000_preview.png
label_preview/WET_label/merged_000000_preview.png
```

ถ้าต้องการรันเฉพาะชุดเดียว ให้แก้ตัวแปรนี้ใน `overlay.py`:

```python
target_label_folder = "WET_label"
```

ถ้าต้องการรันทุกชุด:

```python
target_label_folder = None
```

ค่าที่ควรปรับใน `overlay.py`:

```python
original_root = "original"
json_root = "label"
preview_output_folder = "label_preview"
alpha = 0.45
```

### 2. แปลง JSON เป็น mask อย่างเดียว

ใช้ [trans.py](trans.py) เมื่อต้องการแปลงไฟล์ `.json` จาก LabelMe เป็น mask อย่างเดียว โดยค่า default ตอนนี้ตั้งไว้ที่ชุด `SHADOW_label`

```bash
python trans.py
```

Input:

```text
label/SHADOW_label/*.json
```

Output:

```text
label/SHADOW_masks/*.png
```

สคริปต์นี้ใช้คำสั่งของ LabelMe:

```bash
python -m labelme.cli.json_to_dataset <file.json>
```

ถ้าต้องการแปลงชุดอื่น ให้แก้ path ใน `trans.py`:

```python
json_folder = "label/SHADOW_label"
output_folder = "label/SHADOW_masks"
```

### 3. แปลง JSON เป็น image + label แบบจับคู่กัน

ใช้ [convert_all.py](convert_all.py) เมื่ออยากได้ทั้งภาพต้นฉบับและ mask ที่แปลงจาก LabelMe JSON

```bash
python convert_all.py
```

Input:

```text
labelme_jsons/*.json
```

Output:

```text
converted_all/_img/<name>_img.png
converted_all/_label/<name>_label.png
```

ไฟล์นี้เหมาะกับขั้นตอนก่อนนำข้อมูลไป train model เพราะได้ image และ label เป็นคู่ชื่อเดียวกัน

### 4. Split เป็น train / val / test

ใช้ [split.py](split.py) หลังจากมีโฟลเดอร์ภาพและ label ที่จับคู่กันแล้ว

```bash
python split.py
```

Input default ในไฟล์:

```text
images/
labels/
```

Output:

```text
train/images/
train/labels/
val/images/
val/labels/
test/images/
test/labels/
```

อัตราส่วน split ในไฟล์:

```text
train = 70%
val   = 15%
test  = 15%
```

ถ้าจะใช้กับ output จาก `convert_all.py` ให้แก้ path ใน `split.py` จาก:

```python
image_folder = 'images'
label_folder = 'labels'
```

เป็น:

```python
image_folder = 'converted_all/_img'
label_folder = 'converted_all/_label'
```

### 5. โหลด dataset ด้วย PyTorch

ใช้ [custom_datasets.py](custom_datasets.py) สำหรับโหลดข้อมูลที่อยู่ในรูปแบบ:

```text
converted_all/
  _img/
    frame_0000_img.png
  _label/
    frame_0000_label.png
```

ทดสอบการโหลด:

```bash
python custom_datasets.py
```

### 6. สร้างวิดีโอจากรูปภาพ

ใช้ [create_video.py](create_video.py) เพื่อเรียงรูปภาพในโฟลเดอร์เป็นวิดีโอ

```bash
python create_video.py
```

ค่าที่ควรแก้ในไฟล์:

```python
image_folder = 'NEW_YAML'
video_name = 'new_yaml.mp4'
fps = 5
```

## สรุปความต่างของ 3 ไฟล์หลัก

```text
overlay.py        = ดู/ตรวจ label บนภาพจริง โดยสร้าง overlay preview
trans.py          = แปลง JSON เป็น mask อย่างเดียว
convert_all.py    = แปลง JSON เป็น image + mask เป็นคู่ สำหรับเตรียม dataset
```

ถ้ายังอยู่ในขั้นตอนตรวจ label ให้ใช้ `overlay.py` ก่อน

ถ้าตรวจ label เรียบร้อยแล้วและต้องเตรียมข้อมูล train ค่อยใช้ `convert_all.py` แล้วตามด้วย `split.py`
