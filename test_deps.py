#!/usr/bin/env python3
"""Test sklearn import"""

try:
    import sklearn
    print(f"✅ sklearn imported successfully! Version: {sklearn.__version__}")
except ImportError as e:
    print(f"❌ sklearn import failed: {e}")

try:
    import pandas as pd
    print(f"✅ pandas imported successfully! Version: {pd.__version__}")
except ImportError as e:
    print(f"❌ pandas import failed: {e}")