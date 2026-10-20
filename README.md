# Mall Visitor Counter — Multi-CCTV Starter

Starter untuk >5 RTSP CCTV: YOLO + ByteTrack, directional line crossing, PostgreSQL, Streamlit. Tidak melakukan face recognition.

## Prasyarat
- Python 3.10–3.12 (disarankan 3.11)
- Docker Compose untuk PostgreSQL
- CCTV/NVR dengan RTSP yang dapat diakses komputer pemroses
- Akses jaringan yang sah dan izin dari pengelola CCTV

## Instalasi
1. `cp .env.example .env` dan edit kredensial; jangan commit `.env`.
2. `docker compose --env-file .env up -d db`
3. `python -m venv .venv` dan aktifkan venv.
4. `pip install -r requirements.txt`
5. Muat environment dari `.env` menggunakan mekanisme shell lokal Anda (misalnya `set -a; source .env; set +a` pada bash; hati-hati karakter spesial dalam password). Alternatif gunakan secrets manager.
6. `python -m app.main` untuk pekerja kamera.
7. Di terminal lain, muat environment lalu `streamlit run dashboard/app.py`.
8. Buka alamat lokal Streamlit yang tercetak.

**Penting:** alamat RTSP di `.env.example` hanya placeholder. Gunakan URL aktual. Password yang mengandung karakter khusus di URL RTSP harus di-URL-encode. Jangan mengekspos port PostgreSQL atau dashboard ke internet publik tanpa autentikasi, TLS, dan firewall.

## Konfigurasi kamera
`config/cameras.yaml` memiliki 6 contoh kamera. Hapus kamera yang tidak digunakan. Tambah entri untuk kamera baru, lalu tambahkan variabel RTSP sesuai `env`.
`line` adalah dua koordinat normalisasi (0..1) pada frame setelah resize. `inside_side` menentukan sisi mall. Uji arah di setiap kamera dengan rekaman pendek; balik `inside_side` jika IN/OUT tertukar. Titik pelacakan menggunakan kaki (bottom center) dari bounding box.

## Cara pengujian
1. Jalankan satu kamera lebih dulu.
2. Rekam ground truth manual untuk minimal 100 lintasan masuk/keluar, termasuk orang berdekatan dan berbalik arah.
3. Bandingkan per arah: `abs(prediksi - aktual) / max(aktual,1)` dan tinjau false count serta missed count.
4. Uji RTSP putus, reconnect, pembukaan ulang proses, CPU/GPU dan memori.
5. Perluas ke 6 kamera secara bertahap.

## Batasan starter
- Setiap kamera memakai satu proses YOLO; 6 kamera dapat berat di CPU dan bisa melebihi memori GPU. Untuk produksi, gunakan GPU sizing berdasarkan benchmark, batched inference/shared model, decoding yang efisien, dan supervisor proses.
- `model.track(persist=True)` memakai state tracking per proses; tracker direset pada reconnect. ID bukan identitas global lintas kamera.
- Event disimpan satu per satu. Database outage menyebabkan pemrosesan diulang dan event pada saat gangguan bisa hilang; produksi memerlukan antrean tahan gangguan (durable queue) dan idempotency key.
- Garis menghitung perubahan sisi stabil dengan hysteresis sederhana. Occlusion, tracking ID switch, atau orang yang bergerak dekat garis dapat menyebabkan kesalahan. Kalibrasi tiap kamera diperlukan.
- Dashboard hanya menyajikan statistik, bukan live video. Jangan tampilkan stream CCTV di dashboard tanpa kontrol akses.
- Occupancy = baseline + IN - OUT hanya valid bila semua pintu tercakup dan baseline benar. Baseline `OPENING_OCCUPANCY` adalah untuk awal hari, bukan setiap restart.
- Status proses mati total tidak akan mengirim heartbeat baru; dashboard menandai status stale setelah 30 detik.
- Tidak ada deduplikasi antar-kamera bila area pandang tumpang tindih; tempatkan garis hitung pada akses yang unik.
- Tinjau lisensi Ultralytics dan kewajiban privasi/peraturan sebelum penggunaan komersial.

## Struktur
- `app/main.py`: proses per kamera
- `app/worker.py`: RTSP, YOLO/ByteTrack, event
- `app/crossing.py`: logika lintasan garis
- `app/db.py`: akses database
- `dashboard/app.py`: metrik/grafik/status
- `sql/schema.sql`: tabel dan indeks
- `config/cameras.yaml`: konfigurasi kamera
