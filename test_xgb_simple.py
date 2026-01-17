#!/usr/bin/env python3
"""Simple XGBoost test"""

try:
    import xgboost as xgb
    print(f"✅ XGBoost imported successfully! Version: {xgb.__version__}")
except ImportError as e:
    print(f"❌ XGBoost import failed: {e}")