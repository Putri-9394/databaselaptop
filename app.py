# ==========================================================
# 💻 SPK Laptop - API Flask (Metode SAW) - Versi Supabase
# Dibuat oleh: Putri Padilah (Compatible with Supabase & Railway)
# ==========================================================

from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2  # Ganti mysql-connector menjadi psycopg2
from psycopg2.extras import RealDictCursor
import datetime
import os

app = Flask(__name__)
CORS(app)

# ==========================
# ⚙️ BAGIAN 1 — KONFIGURASI DATABASE
# ==========================
# Masukkan Connection String dari Supabase (Settings > Database > Connection String > URI)
# Di Railway, masukkan nilai ini ke Variable: DATABASE_URL
DB_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres.hnjraytlxloscngqwjth:ntKvwNBuaURx3Z*@aws-1-ap-south-1.pooler.supabase.com:6543/postgres')

def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🔹 {msg}")

def get_db_connection():
    try:
        # PostgreSQL menggunakan koneksi via URL URI
        conn = psycopg2.connect(DB_URL)
        return conn
    except Exception as e:
        log(f"❌ Gagal koneksi ke Supabase (PostgreSQL): {e}")
        return None

# ==========================
# 🎨 BAGIAN 2 — HALAMAN UTAMA
# ==========================
@app.route('/')
def home():
    return '''
    <html>
        <head><title>💻 API SPK Laptop - Supabase</title></head>
        <body style="font-family:sans-serif;text-align:center;padding:50px;background:#1c1c1c;color:white;">
            <h1>⚙️ API SPK Laptop - Metode SAW</h1>
            <p style="color: #3ecf8e;">Terhubung ke Supabase PostgreSQL ✅</p>
            <p>Gunakan endpoint <strong>/api/hitung</strong> untuk perhitungan.</p>
        </body>
    </html>
    '''

# ==========================
# 🧮 BAGIAN 3 — HITUNG SAW
# ==========================
@app.route('/api/hitung', methods=['POST'])
def hitung_saw():
    conn = None
    cursor = None
    try:
        data = request.get_json(force=True)
        required_keys = ['w_harga', 'w_ram', 'w_prosesor', 'w_gpu', 'w_ssd', 'w_berat']
        if not all(k in data for k in required_keys):
            return jsonify({"message": "❗ Data bobot tidak lengkap."}), 400

        bobot = {k.replace('w_', ''): float(v) for k, v in data.items()}
        
        conn = get_db_connection()
        if conn is None:
            return jsonify({"message": "❌ Koneksi database gagal."}), 500

        # RealDictCursor agar hasil query berbentuk Dictionary (seperti MySQL dictionary=True)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Ambil semua data laptop
        cursor.execute("SELECT * FROM laptops")
        laptops = cursor.fetchall()

        if not laptops:
            return jsonify({"message": "❗ Data laptop di database kosong."}), 404

        # 2. Ambil nilai Min/Max
        cursor.execute("""
            SELECT MIN(harga) AS min_harga, MAX(ram) AS max_ram, 
                   MAX(skor_prosesor) AS max_prosesor, MAX(skor_gpu) AS max_gpu, 
                   MAX(ssd) AS max_ssd, MIN(berat) AS min_berat
            FROM laptops
        """)
        minmax = cursor.fetchone()

        hasil = []
        for l in laptops:
            # Perhitungan Normalisasi SAW (Pastikan nama kolom sesuai di Supabase)
            r_harga = float(minmax['min_harga'] / l['harga']) if l['harga'] != 0 else 0
            r_ram = float(l['ram'] / minmax['max_ram']) if minmax['max_ram'] != 0 else 0
            r_prosesor = float(l['skor_prosesor'] / minmax['max_prosesor']) if minmax['max_prosesor'] != 0 else 0
            r_gpu = float(l['skor_gpu'] / minmax['max_gpu']) if minmax['max_gpu'] != 0 else 0
            r_ssd = float(l['ssd'] / minmax['max_ssd']) if minmax['max_ssd'] != 0 else 0
            r_berat = float(minmax['min_berat'] / l['berat']) if l['berat'] != 0 else 0

            skor = (
                bobot['harga'] * r_harga +
                bobot['ram'] * r_ram +
                bobot['prosesor'] * r_prosesor +
                bobot['gpu'] * r_gpu +
                bobot['ssd'] * r_ssd +
                bobot['berat'] * r_berat
            )
            hasil.append({'nama_laptop': l['nama_laptop'], 'skor': round(skor, 4)})

        hasil_urut = sorted(hasil, key=lambda x: x['skor'], reverse=True)
        return jsonify({"message": "✅ Perhitungan SAW berhasil", "hasil": hasil_urut}), 200

    except Exception as e:
        log(f"Error: {e}")
        return jsonify({"message": f"❌ Terjadi kesalahan server: {str(e)}"}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))

    app.run(host='0.0.0.0', port=port)
