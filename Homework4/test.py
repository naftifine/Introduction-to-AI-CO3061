import os
import cv2
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import numpy as np
import pandas as pd

device = torch.device("cpu")
class_names = ['Angry', 'Disgust', 'Fear', 'Happy', 'Neutral', 'Sad', 'Surprise']

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])


print("Đang tải OpenCV Face Detector...")
prototxt_path = "deploy.prototxt"
caffemodel_path = "res10_300x300_ssd_iter_140000.caffemodel"
net = cv2.dnn.readNetFromCaffe(prototxt_path, caffemodel_path)

print("Đang tải mô hình ResNet-18...")

model = models.resnet18(weights=None)
num_ftrs = model.fc.in_features

model.fc = nn.Sequential(
    nn.Dropout(0.5),
    nn.Linear(num_ftrs, 256),
    nn.ReLU(),
    nn.Dropout(0.3),
    nn.Linear(256, 7)
)

model_path = 'resnet18_emotion_best.pth' 

try:
    state_dict = torch.load(model_path, map_location=device, weights_only=True)
    new_state_dict = {k[7:] if k.startswith('module.') else k: v for k, v in state_dict.items()}
    model.load_state_dict(new_state_dict)
except Exception as e:
    print(f"[Lỗi] Không thể load file '{model_path}'. Chi tiết: {e}")
    exit()

model = model.to(device)
model.eval() 


folder_path = 'test_images'
results = []
valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')

if not os.path.exists(folder_path):
    print(f"Thư mục '{folder_path}' không tồn tại.")
    exit()

image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(valid_extensions)]

print(f"\nTìm thấy {len(image_files)} ảnh. Bắt đầu dự đoán...\n")

for img_name in image_files:
    img_path = os.path.join(folder_path, img_name)
    frame = cv2.imread(img_path)
    
    if frame is None:
        print(f"[Lỗi] Không đọc được ảnh {img_name}")
        continue
        
    (h, w) = frame.shape[:2]
    
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
    net.setInput(blob)
    detections = net.forward()
    
    face_found = False
    best_confidence = 0
    best_box = None
    
    for i in range(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.5 and confidence > best_confidence:
            best_confidence = confidence
            best_box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            face_found = True

    if face_found:
        (startX, startY, endX, endY) = best_box.astype("int")
        startX, startY = max(0, startX), max(0, startY)
        endX, endY = min(w - 1, endX), min(h - 1, endY)
        
        face_crop = frame[startY:endY, startX:endX]
        
        if face_crop.size != 0:
            face_crop_rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
            face_pil = Image.fromarray(face_crop_rgb)
            input_tensor = transform(face_pil).unsqueeze(0).to(device)
            
            with torch.no_grad():
                outputs = model(input_tensor)
                _, preds = torch.max(outputs, 1)
                emotion_label = class_names[preds[0].item()]
                
                probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]
                emotion_confidence = probabilities[preds[0].item()].item() * 100
                
            results.append({
                'Tên ảnh': img_name,
                'Dự đoán': emotion_label,
                'Độ tự tin': round(emotion_confidence, 2),
            })
            print(f"✔️ {img_name: <12} --> {emotion_label: <10} ({emotion_confidence:.2f}%)")
    else:
        results.append({
            'Tên ảnh': img_name,
            'Dự đoán': 'N/A',
            'Độ tự tin': 0,
            'Ghi chú': 'Không tìm thấy mặt'
        })
        print(f"{img_name: <12} --> Không tìm thấy mặt người!")

if results:
    df_results = pd.DataFrame(results)
    output_csv = 'resnet18.csv'
    df_results.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"\nĐã lưu kết quả vào file: {output_csv}")