# ML Integration dalam Strategy Tester - Documentation

## Overview
Strategy Tester sekarang terintegrasi penuh dengan **ML Predictor** untuk memberikan analisa prediksi machine learning terhadap setiap trade signal.

## Fitur yang Ditambahkan

### 1. UI Enhancements

#### A. ML Analysis Results Section (Baru)
- **Lokasi**: Di bawah "📊 Backtest Results"
- **Menampilkan**:
  - Model Status: ✅ Trained / ❌ Not Trained
  - ML Trades: Jumlah trades yang memiliki ML prediction
  - ML Accuracy: Akurasi prediksi ML (dalam %)
  - Avg Confidence: Rata-rata confidence score dari semua ML predictions
  - ML Predicted Wins: Jumlah trades yang diprediksi BENAR oleh ML
  - ML Predicted Losses: Jumlah trades yang diprediksi SALAH oleh ML
- **Tombol**: "🧠 Train ML Model" - Untuk melatih model sebelum backtest

#### B. Enhanced Trade History Table
**Kolom Baru**:
- **ML Pred**: Menampilkan prediksi ML untuk trade (BUY/SELL atau —)
- **ML Conf %**: Menampilkan confidence score dari prediksi ML (0-100% atau —)

**Contoh**:
```
# | Date/Time          | Type | Entry   | Exit    | Profit   | ML Pred | ML Conf % | Duration
1 | 2026-01-20 10:30   | BUY  | 2050.25 | 2051.80 | $15.50   | BUY     | 78%       | 45 min
2 | 2026-01-20 11:15   | SELL | 2051.80 | 2050.50 | $13.00   | SELL    | 82%       | 32 min
```

### 2. ML Training Pipeline

#### Workflow:
1. **Setup Symbol**: Masukkan symbol di Configuration (e.g., GOLD, BTC/USD)
2. **Train Model**: Klik "🧠 Train ML Model"
   - Mengumpulkan 30 hari historical data
   - Menghitung technical features
   - Melatih RandomForest & GradientBoosting
   - Menyimpan model untuk backtest
3. **Run Backtest**: Klik "🚀 Run Backtest"
   - Backtester akan menggunakan ML predictions
   - Setiap entry signal divalidasi oleh ML
   - ML confidence score disimpan dengan setiap trade

#### Training Status:
```
[INFO] 🧠 Starting ML Model Training...
[INFO] 📊 Symbol: GOLD
[INFO] ⏳ Collecting historical data (30 days)...
[INFO] 📚 Training models...
[SUCCESS] ✅ ML Model Training Completed!
[INFO]   📈 Training Accuracy: 62.34%
[INFO]   🎯 Test Accuracy: 58.92%
```

### 3. ML-Enhanced Backtester

#### Integration Points:

**File**: `strategy_backtester.py`

**Modifikasi**:
```python
def __init__(self, config, initial_balance=10000, ml_predictor=None):
    # Sekarang terima ML predictor sebagai parameter
    self.ml_predictor = ml_predictor
    self.use_ml = ml_predictor is not None and ml_predictor.is_trained
```

**check_entry() Enhancement**:
- Sebelum membuka posisi, ML predictor memberikan prediction
- ML validation: Jika ML confidence < threshold, entry ditolak
- Setiap trade menyimpan: `ml_prediction` dan `ml_confidence`

**Contoh Implementation**:
```python
if self.use_ml:
    direction, confidence = self.ml_predictor.predict(features)
    if direction is not None:
        ml_prediction = 'BUY' if direction == 1 else 'SELL'
        ml_confidence = confidence * 100
        
        # Validate against signal
        if ml_prediction != signal_type:
            if ml_confidence < threshold:
                return  # Skip entry
```

### 4. Results Calculation

#### ML Metrics di Hasil Backtest:
```python
results = {
    'ml_trades': int,           # Total trades dengan ML prediction
    'ml_accuracy': float,       # % trades yang predicted benar
    'ml_predicted_wins': int,   # Trades ML prediction + actual profit
    'ml_predicted_losses': int, # Trades ML prediction + actual loss
    'ml_avg_confidence': float, # Average confidence dari semua ML predictions
    ...
}
```

#### Calculation Logic:
```
ML Accuracy = (Correct Predictions / Total ML Trades) × 100

Correct = Trade has ML prediction AND (
    (ML predicted direction matches actual trade type AND profit > 0) OR
    (ML predicted direction differs from actual type AND profit < 0)
)
```

## Usage Workflow

### Scenario 1: First Time Setup
```
1. Buka Strategy Tester tab
2. Masukkan Symbol: "GOLD"
3. Klik "🧠 Train ML Model"
   → Tunggu hingga training selesai (2-3 menit)
   → Status berubah menjadi "✅ Trained"
4. Setup backtest parameters (dates, balance, etc)
5. Klik "🚀 Run Backtest"
   → Backtester menggunakan trained ML model
   → Hasil menampilkan ML analysis
```

### Scenario 2: Backtest tanpa ML
```
1. Jika tidak train model, backtest tetap berjalan
2. ML columns akan kosong (—)
3. ML results section akan menampilkan 0 untuk semua metrics
```

### Scenario 3: Reuse Trained Model
```
1. Setelah training berhasil, model tersimpan di memory
2. Bisa run backtest multiple times dengan symbol yang sama
3. Tidak perlu melatih ulang sampai aplikasi di-restart
```

## Configuration

### config.py atau bot config:
```python
{
    'enable_ml': True,                    # Enable/disable ML features
    'ml_confidence_threshold': 60,        # Min confidence untuk accept entry (%)
    'ml_min_confidence': 55,              # Min confidence threshold untuk validation
    'prediction_horizon': 5,              # Bars ahead untuk prediction
    'label_threshold': 0.0001,            # Threshold untuk labeling (BUY/SELL)
}
```

## Performance Tips

### 1. Model Accuracy
- Lebih banyak historical data → lebih akurat
- Diperlukan minimal 100+ trading samples
- Different symbols mungkin butuh re-training

### 2. Backtesting
- ML validation mengurangi entry count
- False positives berkurang, tapi juga profit berkurang
- Fine-tune `ml_confidence_threshold` di config

### 3. Monitoring
- Lihat "ML Accuracy" di hasil → indikator seberapa baik ML predictions
- Bandingkan dengan "Win Rate" → lihat kontribusi ML
- Adjust threshold based on accuracy

## Troubleshooting

### Issue: ML Training Gagal
```
Solution:
1. Pastikan MT5 terhubung
2. Symbol exists di MT5
3. Pastikan ada historical data (minimal 30 hari)
4. Check logs untuk detail error
```

### Issue: ML Predictions Semua —
```
Solution:
1. Model belum di-train
2. Klik "🧠 Train ML Model" terlebih dahulu
3. Tunggu hingga status "✅ Trained"
```

### Issue: ML Accuracy Rendah
```
Solution:
1. Collect lebih banyak data (change training days)
2. Try different ml_confidence_threshold
3. Optimize feature selection di ml_predictor.py
4. Validate feature calculation di strategy_backtester.py
```

## Files Modified

1. **Aventa_HFT_Pro_2026_v7_3_3.py**
   - Added: ML results display UI section
   - Added: ML training button & method
   - Modified: display_backtest_results() untuk ML columns
   - Modified: run_backtest() untuk pass ML predictor ke backtester

2. **strategy_backtester.py**
   - Modified: __init__() untuk accept ml_predictor parameter
   - Modified: check_entry() untuk ML validation
   - Modified: close_position() untuk simpan ML prediction data
   - Added: ML metrics di calculate_results()

3. **ml_predictor.py**
   - Unchanged (existing functionality)
   - Digunakan: .predict() method, .is_trained property

## Future Enhancements

- [ ] Save/load trained ML models ke disk
- [ ] Cross-validation untuk ML models
- [ ] ML model comparison (RF vs GB vs XGBoost)
- [ ] Real-time ML prediction indicators di live trading
- [ ] ML confidence evolution chart
- [ ] Automated threshold optimization
