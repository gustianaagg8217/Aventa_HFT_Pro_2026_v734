#!/usr/bin/env python3
"""Test ML training with XGBoost fixes"""

import sys
import os
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))

try:
    from ml_predictor import MLPredictor
    print("✅ Testing ML training with XGBoost fixes...")

    # Create mock config
    config = {'enable_ml': True}

    # Initialize predictor
    predictor = MLPredictor('EURUSD', config)
    print("✅ ML Predictor initialized")

    # Create mock training data
    np.random.seed(42)
    n_samples = 1000

    # Generate mock OHLCV data
    data = {
        'time': pd.date_range('2024-01-01', periods=n_samples, freq='1min'),
        'open': 1.05 + np.random.randn(n_samples) * 0.01,
        'high': 1.05 + np.random.randn(n_samples) * 0.01 + 0.005,
        'low': 1.05 + np.random.randn(n_samples) * 0.01 - 0.005,
        'close': 1.05 + np.random.randn(n_samples) * 0.01,
        'tick_volume': np.random.randint(100, 1000, n_samples)
    }

    df = pd.DataFrame(data)

    # Test feature engineering
    from ml_predictor import FeatureEngineering
    features_df = FeatureEngineering.calculate_technical_features(df)
    print(f"✅ Feature engineering completed, shape: {features_df.shape}")

    # Remove datetime column that can't be used in training
    if 'time' in features_df.columns:
        features_df = features_df.drop('time', axis=1)
        print(f"✅ Removed datetime column, new shape: {features_df.shape}")

    # Fill any NaN values
    features_df = features_df.fillna(0)
    print(f"✅ Filled NaN values, final shape: {features_df.shape}")

    # Create mock target labels (direction: 0=SELL, 1=BUY)
    # Simple strategy: buy if close > open, sell otherwise
    y = (df['close'] > df['open']).astype(int).values

    print(f"✅ Created target labels, shape: {y.shape}")
    print(f"Buy signals: {np.sum(y)}, Sell signals: {len(y) - np.sum(y)}")

    # Test training
    print("🎯 Starting training...")
    result = predictor.train_models(features_df, y)

    if result and result.get('status') == 'success':
        print("✅ Training completed successfully!")
        print(f"Model type: {result.get('model_type')}")
        print(f"Training samples: {result.get('train_samples')}")
        print(f"Test samples: {result.get('test_samples')}")

        # Check training stats
        if hasattr(predictor, 'training_stats') and predictor.training_stats:
            print("✅ Training stats populated:")
            for key, value in predictor.training_stats.items():
                if isinstance(value, (int, float)):
                    print(f"  {key}: {value:.4f}")
                else:
                    print(f"  {key}: {value}")
        else:
            print("❌ Training stats not populated")

    else:
        print(f"❌ Training failed: {result}")

except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()