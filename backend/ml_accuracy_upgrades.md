# 🚀 Peningkatan Akurasi Finblix: Eksplorasi ML & Rekayasa Fitur

Untuk memenuhi target "riset mendalam dan mengubah metode demi akurasi", beberapa pembaruan besar telah diterapkan secara langsung di tingkat *engine core* (inti pemrosesan algoritma `quant_ml.py` dan pembuatan fitur).

Perbaikan yang diterapkan bertujuan agar akurasi dasar (sebelum difilter oleh *deadband*) naik dari ~50-55% menjadi target **60-65%**, dan setelah difilter (sistem *High Conviction*) berpotensi menyentuh **75-80%**.

## 1. Hyperparameter Tuning Otomatis (`RandomizedSearchCV`)
Sebelumnya, model Machine Learning (`HistGradientBoosting` dan `RandomForest`) dilatih menggunakan parameter konstan / *hard-coded*.
- **Metode Baru**: Kini model algoritma di `quant_ml.py` menggunakan **`RandomizedSearchCV`**. Model akan secara otomatis melakukan komputasi terhadap puluhan kombinasi parameter (seperti `learning_rate`, `max_depth`, `max_leaf_nodes`, `l2_regularization`) untuk mencari **metode terbaik dan paling optimal khusus untuk setiap aset (BBCA vs BTC akan punya tuning beda)** menggunakan optimasi target skor `ROC-AUC`.
- **Dampak**: Model Boosted Trees akan jauh lebih pintar beradaptasi dengan volatilitas *time-series* dari masing-masing mata uang kripto dan saham.

## 2. Advanced Technical & Momentum Features
Menambahkan 5 fitur analisis teknikal kuantitatif baru yang kuat di modul `three_hour_engine.py` (untuk kripto) dan `ml_training_engine.py` (untuk saham):
1. `bb_width_roc` *(Bollinger Band Squeeze/Momentum)*: Menganalisa tingkat perubahan (Rate of Change) dari lebar Bollinger Band. Sangat kuat untuk mendeteksi *Breakout* setelah fase konsolidasi.
2. `vol_roc` *(Volume Momentum)*: Persentase percepatan volume perdagangan (seberapa kencang partisipasi pasar berubah).
3. `rsi_macd_divergence`: Interaksi matematika langsung antara RSI dan indikator MACD Histogram untuk membaca divergensi momentum.
4. `atr_ratio` *(Volatility Regime)*: Rasio fluktuasi jangka pendek terhadap rentang 50-bar, mendeteksi jika aset akan masuk siklus *high volatility*.
5. `trend_strength`: Mengukur kekuatan absolut dari tren secara matematis dari jarak harga terhadap indikator Macro (EMA-50), lalu di-normalisasi dengan ATR.

## 3. Pencegahan Deadlock di Windows
Menurunkan parameter multithreading `n_jobs` menjadi 1 pada `RandomizedSearchCV` dan `RandomForest` untuk memastikan kestabilan saat training berjalan (mencegah python *freeze/deadlock* pada OS Windows di belakang layar).

---

### Tindakan Selanjutnya: Latih Model
Karena `RandomizedSearchCV` menambah beban iterasi komputasi yang dalam, *training* kini akan membutuhkan waktu lebih lama (~30-60 detik per aset). 

Sesuai permintaan Anda, Anda dapat melakukan **training mandiri** dengan mengetik perintah berikut di terminal:

```bash
cd backend
python scratch\train_all.py
```
