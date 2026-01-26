import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms
from PIL import Image
import argparse
import os

# -----------------------------
# Model definition
# -----------------------------
class ConvNeXtEmbedding(nn.Module):
    def __init__(self, embedding_dim=512):
        super().__init__()

        self.backbone = models.convnext_base(
            weights=models.ConvNeXt_Base_Weights.IMAGENET1K_V1
        )
        self.backbone.classifier = nn.Identity()

        self.pool = nn.AdaptiveAvgPool2d(1)

        self.embedding = nn.Sequential(
            nn.Flatten(),
            nn.Linear(1024, embedding_dim),
            nn.BatchNorm1d(embedding_dim)
        )

    def forward(self, x):
        x = self.backbone(x)
        x = self.pool(x)
        x = self.embedding(x)
        x = F.normalize(x, p=2, dim=1)
        return x


# -----------------------------
# Argument parser
# -----------------------------
parser = argparse.ArgumentParser(description="Jaguar Re-Identification Inference")
parser.add_argument("--img1", type=str, required=True, help="Path to first image")
parser.add_argument("--img2", type=str, required=True, help="Path to second image")
parser.add_argument(
    "--model",
    type=str,
    default="models/convnext_arcface_jaguar_final.pth",
    help="Path to trained model weights"
)
parser.add_argument(
    "--threshold",
    type=float,
    default=0.75,
    help="Similarity threshold for same/different decision"
)

args = parser.parse_args()


# -----------------------------
# Load model
# -----------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = ConvNeXtEmbedding()
model.load_state_dict(torch.load(args.model, map_location=device))
model.to(device)
model.eval()

print("✅ Model loaded")


# -----------------------------
# Image preprocessing
# -----------------------------
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# -----------------------------
# Embedding extraction
# -----------------------------
def extract_embedding(image_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    image = Image.open(image_path).convert("RGB")
    image = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        emb = model(image)

    return emb.squeeze(0)


# -----------------------------
# Inference
# -----------------------------
emb1 = extract_embedding(args.img1)
emb2 = extract_embedding(args.img2)

similarity = F.cosine_similarity(
    emb1.unsqueeze(0),
    emb2.unsqueeze(0)
).item()


# -----------------------------
# Output
# -----------------------------
print(f"\nCosine similarity: {similarity:.4f}")

if similarity >= args.threshold:
    print("✅ Likely SAME jaguar")
else:
    print("❌ Likely DIFFERENT jaguars")
