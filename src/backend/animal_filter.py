"""
Stage 0: Animal vs Non-Animal Filter
Uses Vision Transformer for image classification and WordNet for semantic checking
"""

import torch
import numpy as np
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification
try:
    import nltk
    from nltk.corpus import wordnet as wn
    NLTK_AVAILABLE = True
except:
    NLTK_AVAILABLE = False

class AnimalFilter:
    """Filters images to identify if they contain animals"""
    
    def __init__(self, device='cpu'):
        self.device = device
        self.model_name = "google/vit-base-patch16-224"
        self.processor = None
        self.model = None
        self.initialized = False
        
    def initialize(self):
        """Lazy load the model on first use"""
        if self.initialized:
            return
            
        try:
            print("[AnimalFilter] Loading Vision Transformer model...")
            self.processor = AutoImageProcessor.from_pretrained(self.model_name)
            self.model = AutoModelForImageClassification.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            # Initialize NLTK data
            if NLTK_AVAILABLE:
                try:
                    wn.synsets("dog")  # Test if wordnet is available
                except:
                    import nltk
                    print("[AnimalFilter] Downloading NLTK wordnet...")
                    nltk.download("wordnet", quiet=True)
                    nltk.download("omw-1.4", quiet=True)
            
            self.initialized = True
            print("[AnimalFilter] Model loaded successfully")
        except Exception as e:
            print(f"[AnimalFilter] Failed to load model: {e}")
            self.initialized = False
    
    def classify_image_label(self, image):
        """
        Classify image using ViT to get ImageNet label
        
        Args:
            image: PIL Image object
            
        Returns:
            str: ImageNet label
        """
        if not self.initialized:
            self.initialize()
        
        if not self.initialized:
            return "unknown"
        
        try:
            if self.model is None or self.processor is None:
                return "unknown", 0.0
                
            with torch.no_grad():
                inputs = self.processor(images=image, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                outputs = self.model(**inputs)
                
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
                pred_id = torch.argmax(probs, dim=1).item()
                confidence = probs[0, pred_id].item()
                
                label = self.model.config.id2label[pred_id]
                
                return label, confidence
        except Exception as e:
            print(f"[AnimalFilter] Classification error: {e}")
            return "unknown", 0.0
    
    def is_animal_wordnet(self, label):
        """
        Check if label refers to an animal using WordNet
        
        Args:
            label: str, ImageNet label (e.g., "leopard, Panthera pardus")
            
        Returns:
            bool: True if label is an animal
        """
        if not NLTK_AVAILABLE:
            # Fallback: use common animal keywords
            animal_keywords = [
                'dog', 'cat', 'bird', 'fish', 'animal', 'mammal', 'reptile',
                'tiger', 'lion', 'leopard', 'cheetah', 'jaguar', 'puma',
                'elephant', 'giraffe', 'zebra', 'horse', 'cow', 'deer',
                'snake', 'lizard', 'frog', 'turtle', 'eagle', 'owl', 'parrot'
            ]
            return any(kw in label.lower() for kw in animal_keywords)
        
        try:
            # Split because ImageNet labels often have format: "leopard, Panthera pardus"
            words = label.split(",")
            
            for word in words:
                word = word.strip().lower()
                synsets = wn.synsets(word, pos=wn.NOUN)
                
                for syn in synsets:
                    if not syn:
                        continue
                    
                    # Check if this word is a hypernym of animal
                    try:
                        hypernym_closure = syn.closure(lambda s: s.hypernyms())
                        if hypernym_closure:
                            for hyper in hypernym_closure:
                                if hyper and hyper.name() == "animal.n.01":
                                    return True
                    except (AttributeError, RuntimeError, TypeError):
                        pass
                    
                    # Fallback: check direct hypernyms
                    try:
                        hypernyms = syn.hypernyms()
                        if hypernyms:
                            for hyper in hypernyms:
                                if hyper and hyper.name() == "animal.n.01":
                                    return True
                    except (AttributeError, RuntimeError, TypeError):
                        pass
            
            return False
        except Exception as e:
            print(f"[AnimalFilter] WordNet error: {e}")
            # Fallback to keyword matching
            return self.is_animal_wordnet_fallback(label)
    
    def is_animal_wordnet_fallback(self, label):
        """Fallback keyword-based animal detection"""
        animal_keywords = [
            'dog', 'cat', 'bird', 'fish', 'animal', 'mammal', 'reptile',
            'tiger', 'lion', 'leopard', 'cheetah', 'jaguar', 'puma',
            'elephant', 'giraffe', 'zebra', 'horse', 'cow', 'deer',
            'snake', 'lizard', 'frog', 'turtle', 'eagle', 'owl', 'parrot'
        ]
        return any(kw in label.lower() for kw in animal_keywords)
    
    def classify(self, image):
        """
        Classify if image contains an animal
        
        Args:
            image: PIL Image object or numpy array
            
        Returns:
            dict with:
            - is_animal: bool
            - label: str (ImageNet label)
            - confidence: float (0-1)
        """
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image).convert('RGB')
        elif not isinstance(image, Image.Image):
            raise ValueError("Input must be PIL Image or numpy array")
        
        label, confidence = self.classify_image_label(image)
        is_animal = self.is_animal_wordnet(label)
        
        return {
            'is_animal': is_animal,
            'label': label,
            'confidence': confidence
        }
