# 🤖 ML Models - Save & Load Guide

## Workflow: Train → Save → Load → Use

### 1️⃣ Train ML Models
```
ML Models Tab → Training Days (30/60/90) → "🧠 Train Models"
⏳ Wait 2-5 minutes untuk training selesai
✅ Models trained dan siap disave
```

### 2️⃣ Save Models (Persistence)
```
"💾 Save Models" → Select Folder
📁 Folder structure dibuat:
   ml_models_BOT_NAME_SYMBOL_TIMESTAMP/
   ├── direction_model.pkl      (Prediksi arah BUY/SELL)
   ├── confidence_model.pkl     (Confidence score 0-100%)
   └── scaler.pkl              (Feature scaling normalization)
```

**Files yang di-save:**
- `direction_model.pkl` - RandomForest/GradientBoosting untuk prediksi arah
- `confidence_model.pkl` - Model untuk confidence score
- `scaler.pkl` - StandardScaler untuk normalisasi features

### 3️⃣ Load Models (Reuse Training Hasil Lama)
```
"📁 Load Models" → Select folder yang sudah di-save sebelumnya
✅ Models di-load ke memory
🎯 Ready untuk digunakan tanpa training ulang
```

---

## 💡 Use Cases

### Case 1: Reuse Models Besok Hari
```
Hari 1:
- Train ML model (30 menit)
- "💾 Save Models" → C:\MyModels\gold_models_20260120
- Tutup aplikasi

Hari 2:
- Buka aplikasi
- "📁 Load Models" → C:\MyModels\gold_models_20260120
- ✅ Models langsung ready, tidak perlu train lagi!
```

### Case 2: Backup Models
```
Training hasil bagus:
- Save to → C:\Backups\gold_models_best_20260120
- Bisa restore kapan saja jika ada model baru yang worse
```

### Case 3: Model Per Symbol
```
GOLD model  → C:\MLModels\gold_trained_20260120
EURUSD model → C:\MLModels\eurusd_trained_20260120
SILVER model → C:\MLModels\silver_trained_20260120

Bisa load sesuai kebutuhan trading hari itu
```

---

## 📊 Proses Load Models Detail

### Step 1: Select Bot
```
Pilih bot di left panel yang mau pake saved models
(Penting! Models akan di-attach ke bot itu)
```

### Step 2: Click "📁 Load Models"
```
Dialog folder browser terbuka
```

### Step 3: Select Folder
```
Pilih folder yang berisi 3 files:
✓ direction_model.pkl
✓ confidence_model.pkl  
✓ scaler.pkl
```

### Step 4: Validation
```
System check:
- Apakah ada 3 files? ✓
- Apakah files valid? ✓
- Apakah models corrupt? ✓
```

### Step 5: Load & Initialize
```
- Load semua 3 pkl files ke memory
- Initialize MLPredictor dengan loaded models
- Set is_trained = True
- Attach ke bot
```

### Step 6: Ready!
```
Model Status display update:
✅ ENABLED & TRAINED (Active)
🎯 Ready untuk backtest atau live trading
```

---

## ✨ Features Setelah Load Models

### 1. Gunakan di Backtest
```
Strategy Tester tab:
- Run Backtest → akan automatically gunakan loaded ML models
- Setiap trade di-validate oleh ML
- ML Accuracy dihitung berdasarkan loaded model predictions
```

### 2. Gunakan di Live Trading
```
Control Panel:
- "🟢 Start All" → Bot mulai trading
- ML model aktif untuk setiap entry validation
- Signals di-filter berdasarkan ML confidence
```

### 3. View Model Info
```
ML Models Tab → Model Status section:
📊 Bot:        TAGJA XM GOLD
📊 Symbol:     GOLD
📊 Status:     ✅ ENABLED & TRAINED

📈 Direction Model:
   • Training:  52.34%
   • Testing:   51.89%

📈 Confidence Model:
   • Training:  54.12%
   • Testing:   53.45%
```

---

## 🔄 Workflow Diagram

```
┌─────────────────────────────────────────────────────────┐
│  ML MODELS LIFECYCLE                                    │
└─────────────────────────────────────────────────────────┘

1. TRAIN
   Training Days: 30 → [🧠 Train Models]
   ↓
   (2-5 minutes processing)
   ↓
   ✅ Models Trained

2. SAVE
   [💾 Save Models] → Select Folder
   ↓
   Models saved to:
   ml_models_BOT_SYMBOL_TIMESTAMP/
   ├── direction_model.pkl
   ├── confidence_model.pkl
   └── scaler.pkl

3. LOAD (Later)
   [📁 Load Models] → Select saved folder
   ↓
   ✅ Models Loaded to Memory
   ↓
   Model Status: ENABLED & TRAINED

4. USE
   - Backtest → ML validates trades
   - Live Trading → ML filters entries
   - Strategy Validation → ML accuracy metrics
```

---

## ⚠️ Important Notes

### Same Symbol Required
```
❌ WRONG:
- Train on GOLD
- Try to use on EURUSD

✅ CORRECT:
- Train on GOLD
- Use on GOLD (same symbol)
```

### Model Folder Structure
```
Valid folder should contain:

✓ ml_models_TAGJA_XM_GOLD_20260120_143045/
  ├── direction_model.pkl
  ├── confidence_model.pkl
  └── scaler.pkl

✗ INVALID - Missing files:
  ├── direction_model.pkl
  └── confidence_model.pkl
  (scaler.pkl missing!)
```

### Backup Models
```
Simpan di multiple lokasi:
- C:\MLModels\gold_best\
- D:\Backups\ml_models\
- Cloud storage (Google Drive, OneDrive)
```

---

## 🎯 Typical Usage

### Day 1 (Training & Save)
```
09:00 - Market open
09:05 - Train ML model (30 days history)
09:35 - Training complete
09:36 - Click "💾 Save Models"
09:37 - Saved to C:\Trading\ml_models_gold_20260120
09:38 - Run backtest with new models
10:00 - Start live trading
17:00 - Stop trading, save session
```

### Day 2 (Load & Trade)
```
09:00 - Open app
09:01 - Select bot "TAGJA XM GOLD"
09:02 - Click "📁 Load Models"
09:02 - Select C:\Trading\ml_models_gold_20260120
09:03 - ✅ Models loaded!
09:04 - Click "🟢 Start All" → Live trading dengan saved models
```

### Day 3-30 (Reuse Same Models)
```
Just repeat Day 2:
- Load same model folder
- No training needed
- Immediate trading
```

---

## 📈 Advantages

| Feature | Before | After |
|---------|--------|-------|
| **Reuse Training** | ❌ Need retrain | ✅ Load saved models |
| **Time Saved** | 2-5 min per session | 10 seconds load |
| **Model Backup** | ❌ Not saved | ✅ Multiple copies |
| **Model Comparison** | ❌ Can't compare | ✅ Load different versions |
| **Consistency** | ❌ Different each day | ✅ Exact same model |

---

## 🔧 Technical Details

### What's in Each File

**direction_model.pkl**
- RandomForest/GradientBoosting classifier
- Predicts: BUY (1) or SELL (0)
- Input: ~50 technical features
- Output: Direction class + probability

**confidence_model.pkl**
- Separate confidence scorer model
- Input: Same features as direction_model
- Output: Confidence percentage (0-100%)
- Used for signal validation

**scaler.pkl**
- StandardScaler from sklearn
- Normalizes features before prediction
- Ensures consistent feature ranges
- Critical for model accuracy

### Load Process
```python
from ml_predictor import MLPredictor

ml = MLPredictor("GOLD", config)
success = ml.load_models("C:\path\to\ml_models\")

if success and ml.is_trained:
    # Ready for use
    direction, confidence = ml.predict(features)
```

---

## ✅ Verification Checklist

After loading models:

- [ ] Bot selected correctly
- [ ] Model folder exists with 3 files
- [ ] No error messages in logs
- [ ] Model Status shows ✅ TRAINED
- [ ] Symbol matches (GOLD on GOLD)
- [ ] Ready to backtest or trade

---

## 💾 Storage Recommendations

```
C:\Trading\ML_Models\
├── gold_v1_20260110/  (First version)
├── gold_v2_20260115/  (Improved version)
├── gold_best_20260120/  (Best one)
├── eurusd_v1_20260118/
└── silver_v1_20260119/
```

Setiap folder bisa di-load kapan saja tanpa training ulang!

---

## 🚀 Result

✅ **No more waiting for training!**
- Train once, use many times
- Save best models for emergency use
- Compare different model versions
- Consistent predictions every day

