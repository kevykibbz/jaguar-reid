import os
import subprocess
import sys

def has_cuda():
    """Check if CUDA is available in the container"""
    # Method 1: Check nvidia-smi
    try:
        result = subprocess.run(
            ['nvidia-smi'], 
            check=True, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL,
            timeout=5
        )
        print("✓ CUDA detected via nvidia-smi")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass
    
    # Method 2: Check for CUDA in standard paths
    cuda_paths = ['/usr/local/cuda', '/usr/local/cuda/bin']
    if any(os.path.exists(p) for p in cuda_paths):
        print("✓ CUDA detected via filesystem")
        return True
    
    # Method 3: Check environment variables
    if os.environ.get('CUDA_VISIBLE_DEVICES') or os.environ.get('NVIDIA_VISIBLE_DEVICES'):
        print("✓ CUDA detected via environment variables")
        return True
    
    print("✗ No CUDA detected")
    return False

def install_pytorch():
    """Install appropriate PyTorch version based on CUDA availability"""
    
    if has_cuda():
        print("\n🚀 Installing GPU-enabled PyTorch...")
        cmd = [
            'pip', 'install', '--no-cache-dir',
            'torch==2.8.0',
            'torchvision==0.23.0'
        ]
    else:
        print("\n🚀 Installing CPU-only PyTorch (faster download)...")
        cmd = [
            'pip', 'install', '--no-cache-dir',
            'torch==2.8.0+cpu',
            'torchvision==0.23.0+cpu',
            '--extra-index-url', 'https://download.pytorch.org/whl/cpu'
        ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
    
    if result.returncode != 0:
        print(f"\n❌ Installation failed with return code {result.returncode}")
        sys.exit(1)
    
    print("\n✅ PyTorch installation complete!")

if __name__ == '__main__':
    install_pytorch()
