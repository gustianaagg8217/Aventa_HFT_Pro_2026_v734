# 🧠 ML Model Training Guide

## Cara Kerja Tombol "Train ML Model"

### 📋 Proses Lengkap

1. **Initialize MT5** 
   - Tombol mengecek apakah MT5 terminal sudah berjalan
   - Jika tidak, akan tampil error: "Failed to initialize MT5"

2. **Collect Historical Data** (30 hari)
   - Mengambil data M1 (1 menit) terakhir 30 hari
   - Jumlah data: ~43,200 bars (30 hari × 24 jam × 60 menit)
   - Diperlukan untuk melatih model dengan dataset yang cukup

3. **Feature Engineering** 
   - Menghitung technical indicators:
     - Moving averages (SMA, EMA)
     - Momentum indicators
     - Volatility (ATR, Std Dev)
     - Returns & Log Returns
     - Volume indicators
   - Total features: ~50+ technical features

4. **Train ML Models** (MultiModel Ensemble)
   - **RandomForest**: 100 estimators, max_depth=15
   - **GradientBoosting**: 100 estimators, learning_rate=0.1
   - Training/Test Split: 80/20
   - Prediksi arah: **BUY** (1) atau **SELL** (0)

5. **Validation & Metrics**
   - Compute training accuracy
   - Compute test accuracy (generalization)
   - Model siap digunakan di backtest

---

## ⚠️ Penyebab "Failed"

### 1. **MT5 Tidak Running** ❌
```
❌ Failed to initialize MT5
   Make sure MT5 is running
```
**Solusi:**
- Pastikan MetaTrader5 sudah dibuka
- Pastikan connected ke broker (status online)

### 2. **Tidak Ada Data Historis** ❌
```
❌ ML Training Failed!
   Check backtest logs for details
```
**Penyebab:**
- Symbol tidak terdaftar di MT5
- MT5 belum download history untuk symbol tersebut

**Solusi:**
- Verify symbol benar (contoh: GOLD, EURUSD, XAUUSD.o)
- Di MT5, buka chart symbol → right-click → "Download History"

### 3. **Symbol Salah** ❌
```
Collecting 30 days of historical data for INVALID...
Failed to collect historical data
```
**Solusi:**
- Check symbol name di MT5
- Pastikan symbol tersedia di broker

### 4. **Insufficient Data After Preprocessing** ❌
**Penyebab:**
- Data terlalu sedikit setelah feature engineering
- Terlalu banyak NaN values yang di-drop

**Solusi:**
- Gunakan timeframe yang lebih lama (bukan M1)
- Atau increase `days` parameter dari 30 menjadi 60+

---

## ✅ Cara Sukses Training ML Model

### Step 1: Siapkan MT5
```
✓ Buka MetaTrader5 terminal
✓ Pastikan terkoneksi (Account section menunjukkan status)
✓ Buka chart symbol yang ingin dilatih (contoh: GOLD)
✓ Download history jika diperlukan
```

### Step 2: Set Symbol di GUI
```
Masuk tab "Strategy Tester"
- Symbol: GOLD (harus sama seperti di MT5)
- Initial Balance: 1000 (atau sesuai keinginan)
```

### Step 3: Klik "Train ML Model" 🧠
```
Tunggu hingga selesai (bisa 2-5 menit tergantung:
- Ukuran dataset
- Jumlah features
- Performa CPU
```

### Step 4: Monitor Log
```
Lihat tab "Backtest Logs", akan tampil:

🧠 Starting ML Model Training...
📊 Symbol: GOLD
⏳ Collecting historical data (30 days)...
✓ MT5 initialized
📚 Initializing ML predictor for GOLD...
📚 Training models (RandomForest + GradientBoosting)...
✅ ML Model Training Completed!
  📈 Training Accuracy: 52.34%
  🎯 Test Accuracy: 51.89%
```

---

## 📊 ML Model Output

### ML Results Section
```
Model Status:          ✅ Trained
ML Trades:            0 (akan update setelah backtest)
ML Accuracy:          51.89% (dari test set)
Avg Confidence:       0.0% (akan update saat backtest)

ML Predicted Wins:    0 (akan update saat backtest)
ML Predicted Losses:  0 (akan update saat backtest)
```

### Di Backtest Results
Setelah training, saat backtest:
- Setiap entry akan di-validate oleh ML model
- Jika ML confidence < threshold (default 55%), entry di-skip
- Trade history menampilkan:
  - **ML Pred**: Direction yang di-predict (BUY/SELL)
  - **ML Conf %**: Confidence score (0-100%)

---

## 🔧 Troubleshooting Commands

### Debug Mode: Check Logs di Terminal
```powershell
# Jalankan GUI
python Aventa_HFT_Pro_2026_v7_3_3.py

# Output akan tampil di console:
# [Timestamp] [INFO/ERROR] Message
```

### Check ML Predictor Manually
```python
from ml_predictor import MLPredictor
import MetaTrader5 as mt5

# Initialize
mt5.initialize()

# Train
ml = MLPredictor("GOLD", {})
success = ml.train(days=30)
print(f"Training success: {success}")
print(f"Is trained: {ml.is_trained}")

# Predict
features = {...}  # dict of features
direction, confidence = ml.predict(features)
print(f"Direction: {direction}, Confidence: {confidence}")
```

---

## 📈 Interpretasi Accuracy

### Training Accuracy 52-55%
```
✓ NORMAL - Karena:
  - Market tidak selalu predictable 100%
  - HFT timeframes sangat noise
  - 50% = random chance, 52% = slight edge
```

### Training Accuracy > 60%
```
✓ GOOD - Model menemukan pattern yang consistent
```

### Training Accuracy 50% atau dibawah
```
❌ POOR - Model tidak learning:
  - Cek data quality
  - Cek features relevance
  - Cek label distribution (BUY vs SELL ratio)
```

---

## 🚀 Tips Optimasi ML Training

### 1. **Increase Data Size**
```python
# Default: 30 hari
success = ml_predictor.train(days=60)  # 60 hari
```

### 2. **Better Features**
Edit `ml_predictor.py` → `FeatureEngineering.calculate_technical_features()`

### 3. **Different Symbols**
- Emas (GOLD) = sangat volatile, bagus untuk ML
- Forex (EURUSD) = trending lebih clear
- Crypto = high volatility, banyak noise

### 4. **Hyperparameter Tuning**
```python
# Edit train_models() di ml_predictor.py
# RandomForest(n_estimators=200, max_depth=20)
# GradientBoosting(learning_rate=0.05)
```

---

## ✨ Hasil Sukses Training

```
Model Status:     ✅ Trained
ML Trades:        156
ML Accuracy:      53.85%
Avg Confidence:   67.3%
ML Predicted Wins: 84
ML Predicted Losses: 72
```

Ini berarti:
- ✅ Model successfully trained
- 📊 Dari 156 trades yang di-evaluate ML:
  - 84 di-predict sebagai WIN (dengan confidence 67%)
  - 72 di-predict sebagai LOSS
- 📈 Accuracy: 53.85% (slightly better than random)

---

## 🔐 Notes

1. **ML adalah Optional**
   - Backtest bisa berjalan tanpa ML (hanya technical signals)
   - ML hanya enhance entry validation, bukan replace signals

2. **Model Tidak Saved**
   - Setiap training, model dibuat dari scratch
   - TODO: Save/Load trained models ke disk

3. **Single Thread**
   - Training berjalan di background thread
   - GUI tetap responsive

4. **Configuration**
   - ML config tersimpan di bot config
   - Setiap bot bisa punya ML predictor berbeda

---

## 📞 Quick Debug

| Error | Cause | Fix |
|-------|-------|-----|
| ❌ Failed to initialize MT5 | MT5 not running | Open MT5 terminal |
| ❌ Failed to import ML predictor | ml_predictor.py missing | Check file exists |
| ❌ ML Training Failed | Data collection error | Download history in MT5 |
| ✅ Trained but 50% accuracy | Model not finding patterns | Try different symbol |

