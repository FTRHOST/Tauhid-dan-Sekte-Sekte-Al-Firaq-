import fitz  # PyMuPDF
import google.generativeai as genai
from PIL import Image
import time
import os
import subprocess
from dotenv import load_dotenv  # Import library dotenv

# ==========================================
# KONFIGURASI API KEY GEMINI (AMAN)
# ==========================================
# Muat variabel dari file .env
load_dotenv()

# Ambil API_KEY dari environment variable
API_KEY = os.getenv("GEMINI_API_KEY")

# Validasi agar program berhenti jika .env lupa diisi
if not API_KEY:
    raise ValueError("API Key tidak ditemukan! Pastikan file .env sudah ada dan berisi GEMINI_API_KEY.")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def push_to_github(folder_path, page_num):
    """Fungsi untuk melakukan git add, commit, dan push per halaman"""
    try:
        # 1. Git Add
        subprocess.run(["git", "add", folder_path], check=True, stdout=subprocess.DEVNULL)
        
        # 2. Git Commit
        commit_message = f"Auto-commit: Tambah hasil translasi halaman {page_num}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True, stdout=subprocess.DEVNULL)
        
        # 3. Git Push
        subprocess.run(["git", "push"], check=True, stdout=subprocess.DEVNULL)
        
        print(f"    [GIT] Berhasil push halaman {page_num} ke GitHub 🚀")
    except subprocess.CalledProcessError as e:
        print(f"    [GIT INFO] Lewati Git push: Tidak ada perubahan baru atau terjadi masalah")

def translate_pdf_structured(pdf_path, start_page=1, end_page=None, base_folder='hasil_terjemahan_ai'):
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Gagal membuka PDF: {e}")
        return

    total_pages = len(doc)
    if end_page is None or end_page > total_pages:
        end_page = total_pages
    if start_page < 1:
        start_page = 1

    print(f"Mulai proses dari halaman {start_page} sampai {end_page}...")

    for page_index in range(start_page - 1, end_page):
        human_page_num = page_index + 1
        page_folder = os.path.join(base_folder, f"page-{human_page_num}")
        os.makedirs(page_folder, exist_ok=True)
        
        try:
            print(f"\n[*] Memproses Halaman {human_page_num}...")
            page = doc.load_page(page_index)
            
            # --- PROSES EKSTRAKSI GAMBAR ---
            zoom_matrix = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=zoom_matrix)
            image_path = os.path.join(page_folder, f"gambar_page_{human_page_num}.png")
            pix.save(image_path)
            
            # --- PROSES GEMINI AI ---
            img_to_process = Image.open(image_path)
            prompt = """
            Tolong bertindak sebagai penerjemah profesional. 
            1. Ekstrak teks bahasa Arab yang ada di dalam gambar ini.
            2. Terjemahkan teks tersebut ke dalam bahasa Indonesia.
            
            Berikan hasil dengan format yang rapi:
            [Teks Arab]
            (isi teks arab)
            
            [Terjemahan]
            (isi terjemahan)
            """
            
            response = model.generate_content([prompt, img_to_process])
            final_text = response.text
            
            # --- SIMPAN TEKS ---
            text_path = os.path.join(page_folder, f"terjemahan_page_{human_page_num}.txt")
            with open(text_path, 'w', encoding='utf-8') as text_file:
                text_file.write(final_text)
                
            print(f"    [SUCCESS] File tersimpan di '{page_folder}/'")

            # --- OTOMATISASI GIT ---
            push_to_github(page_folder, human_page_num)

            # Jeda untuk API Limit
            time.sleep(5)
            
        except Exception as e:
            print(f"    [ERROR] Gagal memproses halaman {human_page_num}: {e}")

    print(f"\nSelesai! Semua data sudah diproses.")

# ==========================================
# CARA PENGGUNAAN
# ==========================================
if __name__ == "__main__":
    file_input = "buku_arab.pdf"  # Ganti dengan nama PDF kamu
    
    translate_pdf_structured(
        pdf_path=file_input, 
        start_page=1, 
        end_page=5, 
        base_folder='hasil_terjemahan_ai'
    )
