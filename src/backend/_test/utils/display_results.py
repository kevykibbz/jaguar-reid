#!/usr/bin/env python3
"""Display Stage 1 test results in tabular format"""

print("\n" + "="*110)
print("STAGE 1 BINARY CLASSIFICATION TEST RESULTS".center(110))
print("="*110)

print(f"\n{'Image':<15} {'Expected':<12} {'Predicted':<12} {'BigCat%':<15} {'NotBigCat%':<15} {'Status':<10}")
print("-"*110)

results_data = [
    ("Jaguar", "BigCat", "BigCat", "99.96%", "0.04%", "PASS"),
    ("Dog", "NotBigCat", "BigCat", "70.59%", "29.41%", "FAIL"),
    ("Elephant", "NotBigCat", "NotBigCat", "0.05%", "99.95%", "PASS"),
    ("Tiger", "BigCat", "BigCat", "100.00%", "0.00%", "PASS"),
    ("Lion", "BigCat", "BigCat", "99.98%", "0.02%", "PASS"),
    ("Leopard", "BigCat", "BigCat", "100.00%", "0.00%", "PASS"),
    ("Cheetah", "BigCat", "BigCat", "100.00%", "0.00%", "PASS"),
]

pass_count = 0
for img, expected, predicted, bigcat, notbigcat, status in results_data:
    print(f"{img:<15} {expected:<12} {predicted:<12} {bigcat:<15} {notbigcat:<15} {status:<10}")
    if status == "PASS":
        pass_count += 1

print("="*110)

total_images = len(results_data)
bigcats = sum(1 for _, expected, _, _, _, _ in results_data if expected == "BigCat")
notbigcats = sum(1 for _, expected, _, _, _, _ in results_data if expected == "NotBigCat")

bigcats_correct = sum(1 for _, expected, predicted, _, _, status in results_data 
                      if expected == "BigCat" and predicted == "BigCat" and status == "PASS")
notbigcats_correct = sum(1 for _, expected, predicted, _, _, status in results_data 
                         if expected == "NotBigCat" and predicted == "NotBigCat" and status == "PASS")

print(f"\nSUMMARY")
print("-"*110)
print(f"Total Accuracy:          {pass_count}/{total_images} ({100*pass_count/total_images:.1f}%)")
print(f"BigCat Detection Rate:   {bigcats_correct}/{bigcats} ({100*bigcats_correct/bigcats:.1f}%)")
print(f"NotBigCat Detection Rate: {notbigcats_correct}/{notbigcats} ({100*notbigcats_correct/notbigcats:.1f}%)")
print("\n" + "="*110 + "\n")
