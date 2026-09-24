import os
from PIL import Image
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms.functional as TF

class CustomSegmentationDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.image_dir = os.path.join(root_dir, "_img")
        self.label_dir = os.path.join(root_dir, "_label")
        self.transform = transform

        # ค้นหาไฟล์ภาพทั้งหมดที่ลงท้ายด้วย _img.png
        self.image_files = sorted([
            f for f in os.listdir(self.image_dir) if f.endswith("_img.png")
        ])

    def __len__(self):
        return len(self.image_files)

    def __getitem__(self, idx):
        img_name = self.image_files[idx]
        label_name = img_name.replace("_img.png", "_label.png")

        img_path = os.path.join(self.image_dir, img_name)
        label_path = os.path.join(self.label_dir, label_name)

        # โหลดรูปและเลเบล
        image = Image.open(img_path).convert("RGB")
        label = Image.open(label_path)

        if self.transform:
            image, label = self.transform(image, label)
        else:
            image = TF.to_tensor(image)
            label = TF.pil_to_tensor(label).long().squeeze(0)  # [H, W]

        return image, label


# 🔍 โค้ดทดสอบเมื่อรันไฟล์โดยตรง
if __name__ == "__main__":
    print("📂 กำลังโหลด Dataset จากโฟลเดอร์ 'converted_all'")
    dataset = CustomSegmentationDataset(root_dir="converted_all")
    dataloader = DataLoader(dataset, batch_size=2, shuffle=True)

    for images, labels in dataloader:
        print("✅ ขนาดภาพ:", images.shape)    # [B, 3, H, W]
        print("✅ ขนาดเลเบล:", labels.shape)  # [B, H, W]
        break
