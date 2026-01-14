import os
import pickle

# GANTI INI dengan path folder Anda
folder_path = r"D:\Aventa AI\Project Aventa\Aventa_HFT_Pro_2026_v732\TrainingBTCUSDfutu\ml_models_BTCUSD_futu_20260103_121117"

print(f"Testing load from: {folder_path}")
print("="*60)

# List files
files = os.listdir(folder_path)
print(f"Files in folder: {files}")
print()

# Try to load each file
for filename in files:
    if filename.endswith('.pkl'):
        filepath = os.path.join(folder_path, filename)
        size = os.path.getsize(filepath)
        print(f"Loading: {filename} ({size} bytes)")
        
        try: 
            with open(filepath, 'rb') as f:
                obj = pickle.load(f)
                print(f"  ✓ Loaded: {type(obj).__name__}")
                print(f"  ✓ Object is not None: {obj is not None}")
        except Exception as e: 
            print(f"  ❌ Error:  {e}")
        
        print()

print("="*60)
print("Test complete!")