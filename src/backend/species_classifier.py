"""
Species Classification Module
Jaguar validation classifier using EfficientNet-B0.

NOTE: Current model trained on 31 individual jaguars from Kaggle re-id competition.
Logic: High confidence (>60%) on any of the 31 classes → it's a jaguar
       Low confidence (<60%) → likely NOT a jaguar (e.g., zebra, leopard, etc.)

This approach works because all 31 classes are jaguars. If the model recognizes
the pattern as matching one of the known jaguars, we know it's a jaguar species.
If it doesn't match any jaguar pattern, it's likely a different animal.
"""
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import io

# NOTE: SPECIES_CLASSES kept for reference, but current model uses 31 jaguar IDs
# Future: Retrain with multi-species dataset using these 7 classes
SPECIES_CLASSES = ['jaguar', 'leopard', 'tiger', 'cheetah', 'zebra', 'horse', 'dog']


class SpeciesClassifier(nn.Module):
    """EfficientNet-B0 based species classifier"""
    
    def __init__(self, num_classes=7, pretrained=False):
        super().__init__()
        
        # Load EfficientNet-B0 backbone
        self.backbone = models.efficientnet_b0(weights=None)
        
        # Replace classifier head
        in_features = self.backbone.classifier[1].in_features
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(p=0.3, inplace=True),
            nn.Linear(in_features, num_classes)
        )
    
    def forward(self, x):
        return self.backbone(x)


# Image preprocessing transforms
species_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


def load_species_classifier(model_path, device='cpu'):
    """
    Load trained species classifier from checkpoint.
    
    Args:
        model_path: Path to .pth checkpoint file
        device: Device to load model on ('cpu' or 'cuda')
    
    Returns:
        Loaded model in eval mode, classes list, transform
    """
    checkpoint = torch.load(model_path, map_location=device)
    
    # Get num_classes from checkpoint (dynamically)
    num_classes = checkpoint.get('num_classes', 31)  # Default to 31 if not found
    
    model = SpeciesClassifier(num_classes=num_classes)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    model.eval()
    
    print(f"✓ Loaded species classifier")
    print(f"  Classes: {num_classes}")
    print(f"  Val accuracy: {checkpoint.get('val_acc', 'N/A'):.2f}%")
    
    # Return model, classes (empty list for now since we don't have names), and transform
    return model, None, species_transform


def classify_species(image_bytes, model, device='cpu', return_all_probs=False):
    """
    Validate if image contains a jaguar (vs other animals).
    
    NOTE: This model was trained on 31 individual jaguars from Kaggle competition.
    Logic: If model confidently predicts ANY of the 31 jaguar classes → it's a jaguar
           If model is uncertain/low confidence → likely not a jaguar
    
    Args:
        image_bytes: Raw image bytes (JPEG/PNG)
        model: Loaded species classifier model
        device: Device model is on
        return_all_probs: If True, return probabilities for all classes
    
    Returns:
        dict with keys:
            - species: "jaguar" if confident, "unknown" if not
            - confidence: Max confidence score 0-1 (float)
            - is_jaguar: True if confident it's a jaguar (bool)
    """
    # Load and preprocess image
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    image_tensor = species_transform(image).unsqueeze(0).to(device)
    
    # Run inference
    with torch.no_grad():
        outputs = model(image_tensor)
        probabilities = torch.softmax(outputs, dim=1)
        confidence, predicted_idx = probabilities.max(1)
    
    confidence_score = confidence.item()
    
    # Since all 31 classes are jaguars, high confidence means it's a jaguar
    # Low confidence means it doesn't match any known jaguar → likely not a jaguar
    is_jaguar = confidence_score >= 0.60  # 60% threshold
    species = "jaguar" if is_jaguar else "unknown"
    
    result = {
        'species': species,
        'confidence': confidence_score,
        'is_jaguar': is_jaguar,
        'predicted_class': int(predicted_idx.item())
    }
    
    if return_all_probs:
        # Get top 3 predictions
        top_k = min(3, probabilities.size(1))
        top_probs, top_indices = probabilities[0].topk(top_k)
        result['top_3'] = [(int(idx), float(prob)) for idx, prob in zip(top_indices, top_probs)]
    
    return result


def classify_from_pil_image(pil_image, model, device='cpu'):
    """
    Validate if PIL image contains a jaguar (vs other animals).
    
    NOTE: Model trained on 31 individual jaguars. High confidence = jaguar,
          low confidence = likely not a jaguar.
    
    Args:
        pil_image: PIL Image object (RGB)
        model: Loaded species classifier model
        device: Device model is on
    
    Returns:
        dict with species classification results
    """
    image_tensor = species_transform(pil_image).unsqueeze(0).to(device)
    
    with torch.no_grad():
        outputs = model(image_tensor)
        probabilities = torch.softmax(outputs, dim=1)
        confidence, predicted_idx = probabilities.max(1)
    
    confidence_score = confidence.item()
    
    # High confidence means matches a known jaguar → it's a jaguar
    # Low confidence means doesn't match any jaguar → likely not a jaguar
    is_jaguar = confidence_score >= 0.60  # 60% threshold
    species = "jaguar" if is_jaguar else "unknown"
    
    return {
        'species': species,
        'confidence': confidence_score,
        'is_jaguar': is_jaguar,
        'predicted_class': int(predicted_idx.item())
    }
