#!/usr/bin/env python3
"""Test ML Predictor training with XGBoost fixes"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

try:
    from ml_predictor import MLPredictor
    print("✅ ML Predictor imported successfully")

    # Test initialization
    config = {'enable_ml': True}
    predictor = MLPredictor('EURUSD', config)
    print("✅ ML Predictor initialized successfully")

    # Check training_stats attribute
    if hasattr(predictor, 'training_stats'):
        print("✅ training_stats attribute exists")
        print(f"Initial training_stats: {predictor.training_stats}")
    else:
        print("❌ training_stats attribute missing")

    print("🎯 Ready to test training...")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()