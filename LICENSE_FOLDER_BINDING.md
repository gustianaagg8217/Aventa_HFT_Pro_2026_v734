# 🔐 Sistem Lisensi - Folder Binding Enhancement

## Ringkasan Perubahan

Sistem lisensi telah diperkuat untuk mengikat serial number ke folder instalasi spesifik. Ini meningkatkan keamanan dan mencegah penggunaan ulang lisensi dengan memindahkan program ke folder berbeda.

## Fitur Baru

### 1. Hardware ID Termasuk Folder Path
- **Sebelumnya**: Hardware ID hanya berdasarkan MAC address, CPU ID, Disk Serial, dan Hostname
- **Sekarang**: Hardware ID juga mencakup folder instalasi aplikasi
- **File**: `license_manager.py` - Class `HardwareIDGenerator`

```python
# Hardware ID sekarang termasuk:
hardware_info = [
    MAC_ADDRESS,
    PROCESSOR_ID,
    DISK_SERIAL,
    HOSTNAME,
    INSTALLATION_FOLDER  # ← BARU!
]
```

### 2. Serial Number Terikat ke Folder Spesifik
- Serial number yang dihasilkan hanya berlaku di folder tempat program diinstal
- Jika program dipindahkan ke folder lain, lisensi menjadi **INVALID**
- User harus memasukkan serial number baru untuk folder baru

### 3. Deteksi Perubahan Folder
Sistem dapat mendeteksi dan memberikan pesan yang jelas:

```
❌ PROGRAM DIPINDAHKAN KE FOLDER BERBEDA!

Folder Sebelumnya: C:\USERS\...\AVENTA_HFT_PRO_2026_V735
Folder Saat Ini: C:\USERS\...\AVENTA_HFT_PRO_2026_V736

Program harus diaktifkan ulang dengan Serial Number baru 
ketika dipindahkan ke folder lain.

Silakan gunakan Serial Generator untuk aktivasi ulang.
```

## File yang Diubah

### 1. **license_manager.py**
- ✅ Tambahkan method `get_installation_folder()` di class `HardwareIDGenerator`
- ✅ Update `get_hardware_id()` untuk termasuk folder path
- ✅ Update `verify_license()` untuk deteksi perubahan folder
- ✅ Tambahkan helper methods:
  - `_extract_folder_from_license()` - Ekstrak info folder dari license
  - `_is_folder_mismatch_only()` - Detect apakah hanya folder yang berbeda

### 2. **serial_generator.py**
- ✅ Update class `HardwareIDGenerator`:
  - Tambahkan `get_installation_folder()`
  - Tambahkan folder path ke hardware ID generation
- ✅ Update GUI untuk tampilkan informasi folder:
  - Tampilkan folder instalasi saat ini
  - Tampilkan warning jika program dipindahkan
- ✅ Update log messages untuk informatif tentang folder binding

## Alur Kerja

### Aktivasi Pertama Kali
1. User membuka Serial Generator
2. Generator menampilkan folder instalasi saat ini
3. User memilih opsi "Generate Hardware ID"
4. Hardware ID dihasilkan termasuk folder path
5. Serial number dihasilkan terikat ke folder ini
6. User menerima serial number yang hanya berlaku di folder ini

### Jika Program Dipindahkan
1. User memindahkan folder program ke lokasi baru
2. Saat program dijalankan, license validation gagal
3. Sistem mendeteksi perubahan folder dan memberikan pesan:
   ```
   ❌ PROGRAM DIPINDAHKAN KE FOLDER BERBEDA!
   ```
4. User harus:
   - Membuka Serial Generator di folder baru
   - Generate Hardware ID baru (dengan folder baru)
   - Generate Serial Number baru
   - Masukkan serial number untuk aktivasi

## Implementasi Teknis

### Hardware ID Generation dengan Folder
```python
# Sebelumnya (simplified)
combined = f"{mac_address}|{cpu_id}|{disk_serial}|{hostname}"
hardware_id = hash(combined)

# Sekarang
installation_folder = os.path.abspath(__file__).upper()
combined = f"{mac_address}|{cpu_id}|{disk_serial}|{hostname}|{installation_folder}"
hardware_id = hash(combined)  # Berbeda jika folder berbeda!
```

### Serial Validation
```python
# Validation tetap sama, tapi hardware_id sekarang sudah termasuk folder
def validate_serial(serial, hardware_id):
    hw_check = md5(hardware_id).hexdigest()[:4]
    serial_hw_check = serial.split('-')[-1]
    return hw_check == serial_hw_check
```

## Kelebihan Keamanan

| Aspek | Sebelumnya | Sekarang |
|-------|-----------|---------|
| Binding | Hardware saja | Hardware + Folder |
| Copy Portable | Bisa dipindah-pindah | Harus aktivasi ulang |
| Single License | Gunakan di multiple folder | Locked ke satu folder |
| Usage Tracking | Sulit detect | Jelas terdeteksi |

## Frekuensi Aktivasi

### Scenario 1: Normal Usage
```
C:\Program Files\Aventa → Sekali aktivasi → Serial terikat folder ini
```

### Scenario 2: Portable Usage
```
C:\Program Files\Aventa → Aktivasi 1
D:\Portable\Aventa → Aktivasi 2 (folder beda)
E:\Mobile\Aventa → Aktivasi 3 (folder beda)
```
→ Memerlukan 3 serial number berbeda

## Testing Checklist

- [ ] Generate Hardware ID menampilkan folder instalasi saat ini
- [ ] Serial number berubah ketika Hardware ID berubah (folder berubah)
- [ ] Jika folder dipindah, license validation gagal dengan pesan folder mismatch
- [ ] Error message memberikan informasi folder sebelumnya vs sekarang
- [ ] Serial Generator GUI menampilkan warning tentang folder binding
- [ ] Multiple folder bisa punya serial number berbeda

## Catatan Penting

1. **Folder Path Format**: Menggunakan absolute path dan normalized (uppercase) untuk consistency
2. **Case Sensitivity**: Path di-normalize agar tidak terganggu case (Windows)
3. **Backward Compatibility**: License lama tidak akan tervalidasi di sistem baru ini (intentional)
4. **Reset Option**: Jika hardware berubah total, user bisa generate serial baru

## User Education

Informasi yang harus dikomunikasikan ke user:

1. **Saat Aktivasi**:
   ```
   📁 Folder instalasi Anda: C:\Users\...\Aventa_HFT_Pro_2026_v736
   ⚠️ Serial number ini HANYA berlaku di folder ini
   ```

2. **Jika Ingin Pindah Folder**:
   ```
   Jika Anda ingin pindahkan program ke folder lain:
   1. Pindahkan folder aplikasi ke lokasi baru
   2. Buka Serial Generator di folder baru
   3. Generate Hardware ID dan Serial Number baru
   4. Gunakan serial number baru untuk aktivasi
   ```

3. **Portable Usage**:
   ```
   Jika ingin portable (multiple folder):
   Setiap folder memerlukan serial number terpisah
   Hubungi support untuk informasi lisensi multi-folder
   ```
