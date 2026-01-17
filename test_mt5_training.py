#!/usr/bin/env python3
"""Test ML training with MT5-like data"""

import sys
import os
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))

try:
    from ml_predictor import MLPredictor, FeatureEngineering
    print("✅ ML Predictor imported successfully")

    # Create MT5-like mock data (simulating 1 day of M1 GOLD data for faster testing)
    print("📊 Generating MT5-like mock data (1 day GOLD M1)...")

    symbol = "GOLD.ls"
    n_bars = 1 * 24 * 60  # 1 day * 24 hours * 60 minutes = 1440 bars
    base_price = 2500.0  # Typical GOLD price range

    # Generate realistic OHLCV data for GOLD
    np.random.seed(42)

    # Create time index
    start_time = pd.Timestamp('2024-01-10 00:00:00')
    time_index = pd.date_range(start_time, periods=n_bars, freq='1min')

    # Generate price movements with realistic GOLD volatility
    returns = np.random.normal(0, 0.0002, n_bars)  # Higher volatility for GOLD
    prices = base_price * np.exp(np.cumsum(returns))

    # Create OHLC data with GOLD spread (typically 20-50 cents)
    spread = 0.20  # 20 cents spread for GOLD
    highs = prices + np.abs(np.random.normal(0, 0.50, n_bars))  # Higher range for GOLD
    lows = prices - np.abs(np.random.normal(0, 0.50, n_bars))
    opens = prices + np.random.normal(0, spread/4, n_bars)
    closes = prices + np.random.normal(0, spread/4, n_bars)

    # Generate volume data (GOLD typically has lower volume)
    tick_volumes = np.random.randint(10, 100, n_bars)

    # Create DataFrame in MT5 format
    df = pd.DataFrame({
        'time': time_index,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'tick_volume': tick_volumes,
        'spread': np.full(n_bars, 20),  # 20 points spread for GOLD (0.20 USD)
        'real_volume': np.random.randint(100, 1000, n_bars)
    })

    print(f"✅ Generated {len(df)} bars of mock {symbol} data")
    print(f"   Date range: {df['time'].min()} to {df['time'].max()}")
    print(".2f")
    print(".2f")

    # Create mock config for ML
    config = {'enable_ml': True}

    # Initialize ML Predictor
    predictor = MLPredictor(symbol, config)
    print("✅ ML Predictor initialized")

    # Feature engineering
    print("🔧 Performing feature engineering...")
    features_df = FeatureEngineering.calculate_technical_features(df)
    print(f"✅ Feature engineering completed, shape: {features_df.shape}")

    # Remove datetime column
    if 'time' in features_df.columns:
        features_df = features_df.drop('time', axis=1)
        print(f"✅ Removed datetime column, new shape: {features_df.shape}")

    # Fill NaN values
    features_df = features_df.fillna(method='bfill').fillna(0)
    print(f"✅ Filled NaN values, final shape: {features_df.shape}")

    # Create target labels (simple strategy: buy if close > open)
    y = (df['close'] > df['open']).astype(int).values
    print(f"✅ Created target labels, shape: {y.shape}")
    print(f"   Buy signals: {np.sum(y)}, Sell signals: {len(y) - np.sum(y)}")
    print(".1f")

    # Train models
    print("🎯 Starting ML training with MT5-like data...")
    result = predictor.train_models(features_df, y)

    if result and result.get('status') == 'success':
        print("✅ Training completed successfully!")
        print(f"📊 Model type: {result.get('model_type')}")
        print(f"📊 Training samples: {result.get('train_samples')}")
        print(f"📊 Test samples: {result.get('test_samples')}")

        # Show metrics
        metrics = result.get('metrics', {})
        for model_name, scores in metrics.items():
            print(f"📈 {model_name}:")
            for score_type, value in scores.items():
                print(".4f")

        # Check training stats
        if hasattr(predictor, 'training_stats') and predictor.training_stats:
            print("✅ Training stats populated:")
            stats = predictor.training_stats
            print(f"   Model type: {stats.get('model_type')}")
            print(".4f")
            print(".4f")
            print(".4f")
            print(".4f")
            print(".4f")
            print(".4f")
            print(".4f")
            print(".4f")
            print(f"   Features used: {stats.get('features')}")

            # Show top features if available
            if 'direction_feature_importance' in stats:
                print("🔥 Top Direction Model Features:")
                direction_features = stats['direction_feature_importance']
                sorted_features = sorted(direction_features.items(), key=lambda x: x[1], reverse=True)
                for feature, importance in sorted_features[:5]:
                    print(".4f")

            if 'confidence_feature_importance' in stats:
                print("🔥 Top Confidence Model Features:")
                confidence_features = stats['confidence_feature_importance']
                sorted_features = sorted(confidence_features.items(), key=lambda x: x[1], reverse=True)
                for feature, importance in sorted_features[:5]:
                    print(".4f")

        # Test prediction
        print("🔮 Testing real-time prediction...")
        try:
            # Get latest data point for prediction
            latest_features = features_df.iloc[-1:].values
            direction_pred, confidence = predictor.predict(latest_features)

            print(f"🎯 Latest prediction for {symbol}:")
            print(f"   Direction: {'BUY' if direction_pred == 1 else 'SELL'}")
            print(".3f")

        except Exception as pred_error:
            print(f"⚠️  Prediction test failed: {pred_error}")

    else:
        print(f"❌ Training failed: {result}")

except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()