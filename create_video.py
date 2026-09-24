# source myenv/bin/activate

import cv2
import os

# กำหนดโฟลเดอร์ที่เก็บรูป
image_folder = 'NEW_YAML'  # ชื่อโฟลเดอร์ที่มีรูปภาพ
video_name = 'new_yaml.mp4'  # ชื่อไฟล์วิดีโอที่ต้องการบันทึก
fps = 5  # กำหนดความเร็วเฟรม (เช่น 24 FPS)

# ดึงชื่อไฟล์รูปทั้งหมดในโฟลเดอร์
images = [img for img in os.listdir(image_folder) if img.endswith((".jpg", ".png"))]
images.sort()  # เรียงลำดับชื่อไฟล์

# อ่านรูปภาพแรกเพื่อดูขนาด (กว้าง x สูง)
frame = cv2.imread(os.path.join(image_folder, images[0]))
height, width, layers = frame.shape

# สร้างวิดีโอ
video = cv2.VideoWriter(video_name, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

# เขียนภาพแต่ละภาพลงในวิดีโอ
for image in images:
    img_path = os.path.join(image_folder, image)
    frame = cv2.imread(img_path)
    video.write(frame)

# ปิดการเขียนวิดีโอ
video.release()

print("วิดีโอถูกสร้างแล้ว:", video_name)