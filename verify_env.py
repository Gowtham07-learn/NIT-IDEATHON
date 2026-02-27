import os
import sys
from dotenv import load_dotenv

# Add root to sys.path
sys.path.append(os.getcwd())

def verify():
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        print("FAIL: GEMINI_API_KEY not found in env")
        return
    
    print(f"PASS: Found GEMINI_API_KEY starting with {key[:4]}...")
    
    try:
        from ai.prediction.predictor import DPIPredictor
        predictor = DPIPredictor()
        if predictor.api_key == key:
            print("PASS: DPIPredictor picked up the key automatically")
        else:
            print(f"FAIL: DPIPredictor key mismatch: {predictor.api_key}")
            
        if predictor.model:
            # Depending on SDK version, we check if model is set
            print("PASS: DPIPredictor model configured successfully")
    except Exception as e:
        print(f"FAIL: DPIPredictor initialization failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify()
