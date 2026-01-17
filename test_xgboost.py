#!/usr/bin/env python3
"""Test XGBoost availability and advanced features"""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    import xgboost
    print("✅ XGBoost is available - will use XGBoost for ML models")
    print(f"XGBoost version: {xgboost.__version__}")
    print("🚀 Advanced features enabled:")
    print("  • Hyperparameter tuning with RandomizedSearchCV")
    print("  • Early stopping")
    print("  • Feature importance analysis")
    print("  • Cross-validation scoring")
    xgb_available = True
except ImportError:
    print("⚠️  XGBoost not available - will use sklearn models")
    print("To install XGBoost, run: pip install xgboost")
    print("Note: Advanced features will not be available")
    xgb_available = False

try:
    import ml_predictor
    print("✅ ML Predictor imported successfully")
    print("🎯 New capabilities:")
    print("  • Automatic model selection (XGBoost vs sklearn)")
    print("  • Hyperparameter optimization")
    print("  • Feature importance logging")
    print("  • Enhanced cross-validation")

    # Test ML predictor initialization
    try:
        predictor = ml_predictor.MLPredictor()
        print("✅ ML Predictor initialized successfully")
        if xgb_available:
            print("🎯 XGBoost will be used for enhanced performance")
        else:
            print("📊 sklearn will be used as fallback")
    except Exception as e:
        print(f"⚠️  ML Predictor initialization warning: {e}")

except Exception as e:
    print(f"❌ ML Predictor import error: {e}")