"""
Test image URLs for wildlife classification
Organized by category for easy testing
"""

# Big Cat Images
BIGCAT_IMAGES = {
    "jaguar": {
        "url": "https://inaturalist-open-data.s3.amazonaws.com/photos/618315063/large.jpg",
        "expected_species": "jaguar",
        "description": "Jaguar in natural habitat"
    },
    "tiger": {
        "url": "https://www.shutterstock.com/image-photo/tiger-peacefully-reclined-on-mossy-260nw-2519850751.jpg",
        "expected_species": "tiger",
        "description": "Tiger reclining on mossy surface"
    },
    "lion": {
        "url": "https://media.istockphoto.com/id/1796374503/photo/the-lion-king.jpg?s=612x612&w=0&k=20&c=wDcyZj9yM1-7cCahtCn1SWnu_DGJsOHzlqWt6SSllzU=",
        "expected_species": "lion",
        "description": "Lion portrait"
    },
    "leopard": {
        "url": "https://media.istockphoto.com/id/465470420/photo/focused.jpg?s=612x612&w=0&k=20&c=xjhwOExrjp-u2TFQRh4V7oI5XUlDddm6YF35AR01IZs=",
        "expected_species": "leopard",
        "description": "Focused leopard"
    },
    "cheetah": {
        "url": "https://nationalzoo.si.edu/sites/default/files/animals/cheetah-002.jpg",
        "expected_species": "cheetah",
        "description": "Cheetah at National Zoo"
    }
}

# Other Animals (should be NotBigCat)
OTHER_ANIMALS = {
    "dog": {
        "url": "https://media.istockphoto.com/id/1252455620/photo/golden-retriever-dog.jpg?s=612x612&w=0&k=20&c=3KhqrRiCyZo-RWUeWihuJ5n-qRH1MfvEboFpf5PvKFg=",
        "expected_stage0": "NotAnimal",  # ResNet classifies dog breeds as non-animal
        "expected_stage1": "NotBigCat",
        "description": "Golden Retriever dog"
    },
    "elephant": {
        "url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSmtyzDWvAFEDk5F0D91e-55u_oJU72RdO53A&s",
        "expected_stage1": "NotBigCat",
        "description": "Elephant"
    }
}

# Non-Animals (should be filtered by Stage 0)
NON_ANIMALS = {
    "human": {
        "url": "https://media.istockphoto.com/id/626205158/photo/portrait-of-young-man-with-shocked-facial-expression.jpg?s=612x612&w=0&k=20&c=0SDJDt1crElYppk8F8Qw-MNeBp3Sr8G7cCs4PAHfEH0=",
        "expected_stage0": "NotAnimal",
        "description": "Human portrait"
    },
    "table": {
        "url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTLuLvzmQTf7vu4bfUp250h-KRe6NlyIEbbOA&s",
        "expected_stage0": "NotAnimal",
        "description": "Dining table"
    },
    "chair": {
        "url": "https://www.ikea.com/us/en/images/products/pinntorp-chair-light-brown-stained__1296225_pe935730_s5.jpg",
        "expected_stage0": "NotAnimal",
        "description": "IKEA chair"
    }
}

# All test images combined
ALL_TEST_IMAGES = {**BIGCAT_IMAGES, **OTHER_ANIMALS, **NON_ANIMALS}
