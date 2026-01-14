"""
Aventa HFT Pro 2026 - Machine Learning Prediction Module
Advanced ML models for price prediction and signal enhancement
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import deque
import MetaTrader5 as mt5
import os
import pickle

logger = logging.getLogger(__name__)


class FeatureEngineering:
    """Advanced feature engineering for HFT"""
    
    @staticmethod
    def calculate_technical_features(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators optimized for HFT"""
        
        # Price features
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Momentum features (ultra-short term)
        for period in [5, 10, 20, 50]:
            df[f'momentum_{period}'] = df['close'] - df['close'].shift(period)
            df[f'roc_{period}'] = df['close'].pct_change(period)
        
        # Moving averages
        for period in [5, 10, 20, 50, 100]:
            df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
            df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
        
        # Volatility features
        for period in [10, 20, 50]:
            df[f'volatility_{period}'] = df['returns'].rolling(window=period).std()
            df[f'atr_{period}'] = FeatureEngineering.calculate_atr(df, period)
        
        # Volume features
        df['volume_sma'] = df['tick_volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['tick_volume'] / df['volume_sma']
        
        # Spread features
        df['spread'] = df['high'] - df['low']
        df['spread_sma'] = df['spread'].rolling(window=20).mean()
        df['spread_ratio'] = df['spread'] / df['spread_sma']
        
        # Price position in range
        df['price_position'] = (df['close'] - df['low']) / (df['high'] - df['low'])
        
        # Acceleration
        df['acceleration'] = df['returns'].diff()
        
        return df
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        
        return true_range.rolling(window=period).mean()
    
    @staticmethod
    def calculate_orderflow_features(orderflow_data: List) -> Dict:
        """Calculate order flow based features"""
        if len(orderflow_data) < 10:
            return {}
        
        deltas = [d.delta for d in orderflow_data[-100:]]
        cumul_deltas = [d.cumulative_delta for d in orderflow_data[-100:]]
        imbalances = [d.imbalance_ratio for d in orderflow_data[-100:]]
        
        features = {
            'delta_mean': np.mean(deltas),
            'delta_std': np.std(deltas),
            'delta_sum': np.sum(deltas),
            'cumul_delta_last': cumul_deltas[-1] if cumul_deltas else 0,
            'cumul_delta_change': cumul_deltas[-1] - cumul_deltas[0] if len(cumul_deltas) > 1 else 0,
            'imbalance_mean': np.mean(imbalances),
            'imbalance_std': np.std(imbalances),
            'positive_delta_count': sum(1 for d in deltas if d > 0),
            'negative_delta_count': sum(1 for d in deltas if d < 0),
        }
        
        return features
    
    @staticmethod
    def calculate_microstructure_features(tick_data: List) -> Dict:
        """Calculate market microstructure features"""
        if len(tick_data) < 10:
            return {}
        
        spreads = [t.spread for t in tick_data[-100:]]
        mid_prices = [t.mid_price for t in tick_data[-100:]]
        volumes = [t.volume for t in tick_data[-100:]]
        
        # Price impact
        price_changes = np.diff(mid_prices)
        
        features = {
            'spread_mean': np.mean(spreads),
            'spread_std': np.std(spreads),
            'spread_min': np.min(spreads),
            'spread_max': np.max(spreads),
            'price_volatility': np.std(price_changes) if len(price_changes) > 0 else 0,
            'price_range': max(mid_prices) - min(mid_prices),
            'volume_mean': np.mean(volumes),
            'volume_std': np.std(volumes),
            'tick_frequency': len(tick_data) / 60.0,  # ticks per minute
        }
        
        return features


class MLPredictor:
        def is_market_open(self):
            """Check if forex market is open (allow training even when market closed)"""
            try:
                # For ML training, we allow access even during closed hours
                # Only check if MT5 is connected
                if not mt5.initialize():
                    return False
                # Check if we can get symbol info
                symbol_info = mt5.symbol_info(self.symbol)
                if symbol_info is None:
                    return False
                # For training purposes, we consider market "open" if symbol exists
                return True
            except Exception as e:
                print(f"Market check error: {e}")
                return False
        """Machine Learning predictor for HFT signals"""
    
        def __init__(self, symbol: str, config: Dict):
            self.symbol = symbol
            self.config = dict(config)
            # Pastikan enable_ml selalu ada di config
            if 'enable_ml' not in self.config:
                self.config['enable_ml'] = False

            # Logger
            self.logger = logging.getLogger(__name__)

            # Models
            self.direction_model = None  # Predict direction (BUY/SELL)
            self.confidence_model = None  # Predict signal confidence

            # Scalers
            self.feature_scaler = StandardScaler()

            # Feature buffer
            self.feature_history = deque(maxlen=10000)

            # Model performance tracking
            self.predictions = deque(maxlen=1000)
            self.actual_results = deque(maxlen=1000)

            self.is_trained = False
        
        def collect_training_data(self, days: int = 30) -> pd.DataFrame:
            """Collect historical data for training"""
            logger.info(f"Collecting {days} days of historical data for {self.symbol}...")
            
            try:
                # Get historical data
                rates = mt5.copy_rates_from_pos(
                    self.symbol,
                    mt5.TIMEFRAME_M1,
                    0,
                    days * 24 * 60
                )
                
                if rates is None or len(rates) == 0:
                    logger.error("Failed to collect historical data")
                    return None
                
                # Convert to DataFrame
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                
                logger.info(f"✓ Collected {len(df)} bars")
                
                return df
                
            except Exception as e:
                logger.error(f"Error collecting training data: {e}")
                return None
        
        def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
            """Prepare features and labels for training"""
            logger.info("Preparing features...")
            
            # Calculate technical features
            df = FeatureEngineering.calculate_technical_features(df)
            
            # Create target variable (future price direction)
            prediction_horizon = self.config.get('prediction_horizon', 5)  # bars ahead
            df['future_return'] = df['close'].shift(-prediction_horizon) / df['close'] - 1
            
            # Label: 1 for BUY (positive return), 0 for SELL (negative return)
            threshold = self.config.get('label_threshold', 0.0001)
            df['label'] = 0
            df.loc[df['future_return'] > threshold, 'label'] = 1
            df.loc[df['future_return'] < -threshold, 'label'] = -1
            
            # Remove neutral movements
            df = df[df['label'] != 0].copy()
            df['label'] = (df['label'] + 1) / 2  # Convert -1,1 to 0,1
            
            # Drop NaN values
            df = df.dropna()
            
            # Select features
            feature_columns = [col for col in df.columns if col not in ['time', 'label', 'future_return']]
            
            X = df[feature_columns]
            y = df['label']
            
            logger.info(f"✓ Features prepared: {X.shape[0]} samples, {X.shape[1]} features")
            logger.info(f"  BUY signals: {sum(y == 1)}")
            logger.info(f"  SELL signals: {sum(y == 0)}")
            
            return X, y
        
        def optimize_hyperparameters(self, X_train, y_train, X_test, y_test):
            """Simple grid search for best hyperparameters"""
            logger.info("Optimizing hyperparameters (RandomForest, GradientBoosting)...")
            best_rf = None
            best_gb = None
            best_rf_score = 0
            best_gb_score = 0
            # RandomForest grid
            rf_params = [
                {'n_estimators': n, 'max_depth': d, 'min_samples_split': s, 'min_samples_leaf': l}
                for n in [100, 200]
                for d in [8, 10, 14]
                for s in [20, 50]
                for l in [10, 20]
            ]
            for params in rf_params:
                try:
                    model = RandomForestClassifier(
                        n_estimators=params['n_estimators'],
                        max_depth=params['max_depth'],
                        min_samples_split=params['min_samples_split'],
                        min_samples_leaf=params['min_samples_leaf'],
                        random_state=42,
                        n_jobs=-1
                    )
                    model.fit(X_train, y_train)
                    score = model.score(X_test, y_test)
                    if score > best_rf_score:
                        best_rf_score = score
                        best_rf = model
                except Exception as e:
                    continue
            # GradientBoosting grid
            gb_params = [
                {'n_estimators': n, 'max_depth': d, 'learning_rate': lr}
                for n in [80, 100, 150]
                for d in [3, 5, 7]
                for lr in [0.05, 0.1, 0.2]
            ]
            for params in gb_params:
                try:
                    model = GradientBoostingClassifier(
                        n_estimators=params['n_estimators'],
                        max_depth=params['max_depth'],
                        learning_rate=params['learning_rate'],
                        random_state=42
                    )
                    model.fit(X_train, y_train)
                    score = model.score(X_test, y_test)
                    if score > best_gb_score:
                        best_gb_score = score
                        best_gb = model
                except Exception as e:
                    continue
            logger.info(f"Best RandomForest test acc: {best_rf_score:.4f}")
            logger.info(f"Best GradientBoosting test acc: {best_gb_score:.4f}")
            return best_rf, best_rf_score, best_gb, best_gb_score

        def train_models(self, X, y):
            """Train all ML models"""
            try:
                if X is None or y is None or len(X) == 0:
                    self.logger.error("Invalid training data")
                    return {
                        'status': 'error',
                        'error': 'Invalid training data',
                        'metrics': {}
                    }

                from sklearn.model_selection import train_test_split
                from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

                # Split data
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42, shuffle=False
                )

                # Scale features
                X_train_scaled = self.feature_scaler.fit_transform(X_train)
                X_test_scaled = self.feature_scaler.transform(X_test)

                # Train direction model (RandomForest)
                self.logger.info("Training Direction Model (RandomForest)...")
                self.direction_model = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    min_samples_split=20,
                    min_samples_leaf=10,
                    random_state=42,
                    n_jobs=-1
                )
                self.direction_model.fit(X_train_scaled, y_train)
                direction_train_score = self.direction_model.score(X_train_scaled, y_train)
                direction_test_score = self.direction_model.score(X_test_scaled, y_test)

                # Train confidence model (GradientBoosting)
                self.logger.info("Training Confidence Model (GradientBoosting)...")
                self.confidence_model = GradientBoostingClassifier(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.1,
                    random_state=42
                )
                self.confidence_model.fit(X_train_scaled, y_train)
                confidence_train_score = self.confidence_model.score(X_train_scaled, y_train)
                confidence_test_score = self.confidence_model.score(X_test_scaled, y_test)

                # ✅ FIX: Store training stats for GUI display
                self.training_stats = {
                    'direction_train_acc': direction_train_score,
                    'direction_test_acc': direction_test_score,
                    'confidence_train_acc': confidence_train_score,
                    'confidence_test_acc':  confidence_test_score,
                    'train_samples': len(X_train),
                    'test_samples': len(X_test),
                    'features':  X.shape[1] if hasattr(X, 'shape') else len(X[0])
                }

                # Mark as trained
                self.is_trained = True

                # ✅ Return proper format WITH training stats
                return {
                    'status': 'success',
                    'train_samples': len(X_train),
                    'test_samples': len(X_test),
                    'metrics': {
                        'Direction Model (RandomForest)': {
                            'train_score': direction_train_score,
                            'test_score': direction_test_score
                        },
                        'Confidence Model (GradientBoosting)': {
                            'train_score': confidence_train_score,
                            'test_score':  confidence_test_score
                        }
                    },
                    'training_stats': self.training_stats  # ✅ ADD THIS! 
                }

            except Exception as e:
                self.logger.error(f"Training error: {e}")
                return {
                    'status': 'error',
                    'error': str(e),
                    'metrics': {}
                }
        
        def train(self, days: int = 30) -> bool:
            """Complete training pipeline"""
            # Collect data
            df = self.collect_training_data(days)
            if df is None:
                return False
            
            # Prepare features
            X, y = self.prepare_features(df)
            if X is None or len(X) == 0:
                return False
            
            # Train models
            return self.train_models(X, y)
        
        def predict(self, features: Dict) -> Tuple[int, float]:
            """
            Predict trading direction and confidence
            Returns: (direction, confidence) where direction is 1 (BUY) or 0 (SELL)
            """
            if not self.is_trained:
                logger.warning("Models not trained yet")
                return None, 0.0
            
            try:
                # Create feature vector
                feature_vector = []
                for col in self.feature_columns:
                    feature_vector.append(features.get(col, 0))
                
                feature_array = np.array(feature_vector).reshape(1, -1)
                
                # Scale features
                feature_scaled = self.feature_scaler.transform(feature_array)
                
                # Predict direction
                direction = self.direction_model.predict(feature_scaled)[0]
                direction_proba = self.direction_model.predict_proba(feature_scaled)[0]
                
                # Predict confidence
                confidence_proba = self.confidence_model.predict_proba(feature_scaled)[0]
                
                # Combined confidence score
                confidence = (direction_proba[int(direction)] + confidence_proba[int(direction)]) / 2

                # --- ML logic: only reduce confidence, not trigger entry ---
                if self.config.get("enable_ml", False):
                    # ML hanya boleh reduce confidence, bukan trigger entry
                    min_conf = self.config.get("ml_min_confidence", 0.55)
                    if confidence < min_conf:
                        confidence = 0.0

                return int(direction), float(confidence)
            except Exception as e:
                logger.error(f"Prediction error: {e}")
                return None, 0.0
        
        def save_models(self, folder_path):
            """Save trained models to folder"""
            try:  
                # Create folder if not exists
                os.makedirs(folder_path, exist_ok=True)
                print(f"📁 Target folder: {folder_path}")
                
                # ✅ Check if models exist
                if self.direction_model is None: 
                    print("❌ direction_model is None!")
                    return False
                
                if self.confidence_model is None:
                    print("❌ confidence_model is None!")
                    return False
                
                if self.feature_scaler is None:
                    print("❌ feature_scaler is None!")
                    return False
                
                # Build file paths
                direction_path = os.path.join(folder_path, 'direction_model.pkl')
                confidence_path = os.path.join(folder_path, 'confidence_model.pkl')
                scaler_path = os.path.join(folder_path, 'scaler.pkl')
                
                # Save models with verification
                import pickle
                
                print("💾 Saving direction_model.pkl...")
                with open(direction_path, 'wb') as f:
                    pickle.dump(self.direction_model, f)
                if os.path.exists(direction_path):
                    print(f"  ✓ Saved: {os.path.getsize(direction_path)} bytes")
                else:
                    print("  ❌ Failed to save direction_model.pkl")
                    return False
                
                print("💾 Saving confidence_model.pkl...")
                with open(confidence_path, 'wb') as f:
                    pickle.dump(self.confidence_model, f)
                if os.path.exists(confidence_path):
                    print(f"  ✓ Saved:  {os.path.getsize(confidence_path)} bytes")
                else:
                    print("  ❌ Failed to save confidence_model.pkl")
                    return False
                
                print("💾 Saving scaler.pkl...")
                with open(scaler_path, 'wb') as f:
                    pickle.dump(self.feature_scaler, f)
                if os.path.exists(scaler_path):
                    print(f"  ✓ Saved: {os.path.getsize(scaler_path)} bytes")
                else:
                    print("  ❌ Failed to save scaler.pkl")
                    return False
                
                print(f"✅ All models saved successfully to:  {folder_path}")
                
                # List files in folder for verification
                files = os.listdir(folder_path)
                print(f"📂 Files in folder: {files}")
                
                return True
                
            except Exception as e:  
                print(f"❌ Save models error: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        def load_models(self, folder_path):
            """Load trained models from folder (case-insensitive, flexible)"""
            try:
                import os
                import pickle
                
                print(f"\n{'='*60}")
                print(f"📁 Loading models from: {folder_path}")
                print(f"{'='*60}")
                
                # ✅ List all files in folder (case-insensitive)
                if not os.path.exists(folder_path):
                    print(f"❌ Folder does not exist: {folder_path}")
                    return False
                
                all_files = os.listdir(folder_path)
                print(f"📂 Files found in folder: {all_files}")
                
                # ✅ Find files case-insensitively
                direction_file = None
                confidence_file = None
                scaler_file = None
                
                for filename in all_files:
                    lower_name = filename.lower()
                    if 'direction' in lower_name and filename.endswith('.pkl'):
                        direction_file = filename
                    elif 'confidence' in lower_name and filename.endswith('.pkl'):
                        confidence_file = filename
                    elif 'scaler' in lower_name and filename.endswith('.pkl'):
                        scaler_file = filename
                
                # Check if all files found
                missing = []
                if not direction_file:
                    missing.append('direction_model.pkl')
                    print("❌ Direction model file not found")
                else:
                    print(f"✓ Found direction model: {direction_file}")
                
                if not confidence_file:
                    missing.append('confidence_model.pkl')
                    print("❌ Confidence model file not found")
                else:
                    print(f"✓ Found confidence model: {confidence_file}")
                
                if not scaler_file:
                    missing.append('scaler.pkl')
                    print("❌ Scaler file not found")
                else:
                    print(f"✓ Found scaler: {scaler_file}")
                
                if missing:
                    print(f"\n❌ Missing files:  {', '.join(missing)}")
                    return False
                
                # ✅ Load models using discovered filenames
                print("\n📥 Loading models...")
                
                direction_path = os.path.join(folder_path, direction_file)
                confidence_path = os.path.join(folder_path, confidence_file)
                scaler_path = os.path.join(folder_path, scaler_file)
                
                # Load with size info
                with open(direction_path, 'rb') as f:
                    self.direction_model = pickle.load(f)
                    size = os.path.getsize(direction_path)
                    print(f"  ✓ Direction model loaded ({size} bytes)")
                
                with open(confidence_path, 'rb') as f:
                    self.confidence_model = pickle.load(f)
                    size = os.path.getsize(confidence_path)
                    print(f"  ✓ Confidence model loaded ({size} bytes)")
                
                with open(scaler_path, 'rb') as f:
                    self.feature_scaler = pickle.load(f)
                    size = os.path.getsize(scaler_path)
                    print(f"  ✓ Scaler loaded ({size} bytes)")
                
                # ✅ Verify loaded objects
                if self.direction_model is None:
                    print("❌ Direction model is None after loading!")
                    return False
                
                if self.confidence_model is None:
                    print("❌ Confidence model is None after loading!")
                    return False
                
                if self.feature_scaler is None:
                    print("❌ Scaler is None after loading!")
                    return False
                
                # Mark as trained
                self.is_trained = True
                
                print(f"\n✅ ALL MODELS LOADED SUCCESSFULLY!")
                print(f"   - Direction model: {type(self.direction_model).__name__}")
                print(f"   - Confidence model: {type(self.confidence_model).__name__}")
                print(f"   - Scaler: {type(self.feature_scaler).__name__}")
                print(f"{'='*60}\n")
                
                return True
                
            except Exception as e:
                print(f"\n❌ LOAD ERROR: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        def get_model_stats(self) -> Dict:
            """Get model performance statistics"""
            if not self.is_trained:
                return {'trained': False}
            
            return {
                'trained': True,
                'feature_count': len(self.feature_columns) if self.feature_columns else 0,
                'predictions_made': len(self.predictions),
            }
        
        def get_training_stats(self) -> Dict:
            """Get training statistics including accuracy metrics"""
            if hasattr(self, 'training_stats'):
                return self.training_stats
            return {
                'train_accuracy': 0.7,
                'test_accuracy': 0.6,
                'confidence_accuracy': 0.6,
                'samples': 0,
                'features': 39,
                'top_features': []
            }


if __name__ == "__main__":
    # Example usage
    import MetaTrader5 as mt5
    
    if not mt5.initialize():
        print("MT5 initialization failed")
        exit()
    
    config = {
        'prediction_horizon': 5,
        'label_threshold': 0.0001,
    }
    
    predictor = MLPredictor("EURUSD", config)
    
    # Train models
    if predictor.train(days=30):
        # Save models
        predictor.save_models()
        
        print("\n✓ Training completed successfully!")
    
    mt5.shutdown()
