import fitz  # PyMuPDF
import google.generativeai as genai
from PIL import Image
import time
import os

# ==========================================
# KONFIGURASI API KEY GEMINI
# ==========================================
# Ganti dengan API Key milikmu dari Google AI Studio
API_KEY = "AIzaSyCYHic-wCrYG5WuulfFz0JklFZXgqmaVbA"
genai.configure(api_key=API_KEY)

model = genai.GenerativeModel('gemini-flash-latest')

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

    print(f"Mulai mengekstrak dan menerjemahkan dari halaman {start_page} sampai {end_page}...")

    # Looping per halaman
    for page_index in range(start_page - 1, end_page):
        human_page_num = page_index + 1
        
        # --- MEMBUAT FOLDER STRUKTUR page-[no] ---
        # Contoh: hasil_terjemahan_ai/page-1/
        page_folder = os.path.join(base_folder, f"page-{human_page_num}")
        os.makedirs(page_folder, exist_ok=True)
        
        try:
            print(f"[*] Memproses Halaman {human_page_num}...")
            page = doc.load_page(page_index)
            
            # 1. Ekstrak Halaman ke Gambar dan Simpan ke dalam folder page-[no]
            zoom_matrix = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=zoom_matrix)
            
            # Path untuk menyimpan gambar
            image_path = os.path.join(page_folder, f"gambar_page_{human_page_num}.png")
            pix.save(image_path) # PyMuPDF bisa langsung menyimpan gambar ke lokal
            
            # 2. Siapkan Gambar dan Prompt untuk Gemini
            # Buka gambar yang baru saja disimpan menggunakan Pillow
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
            
            # 3. Kirim ke Gemini API
            response = model.generate_content([prompt, img_to_process])
            final_text = response.text
            
            # 4. Simpan Hasil Terjemahan ke file .txt di folder yang sama
            text_path = os.path.join(page_folder, f"terjemahan_page_{human_page_num}.txt")
            with open(text_path, 'w', encoding='utf-8') as text_file:
                text_file.write(final_text)
                
            print(f"    [SUCCESS] Selesai. Gambar dan teks disimpan di '{page_folder}/'")

            # Jeda untuk menghindari Rate Limit API gratis
            time.sleep(5)
            
        except Exception as e:
            print(f"    [ERROR] Gagal memproses halaman {human_page_num}: {e}")

    print(f"\nSelesai! Semua data terstruktur di dalam folder: '{base_folder}'")


# ==========================================
# CARA PENGGUNAAN
# ==========================================
if __name__ == "__main__":
    file_input = "buku_arab.pdf"  # Pastikan nama file PDF benar
    
    translate_pdf_structured(
        pdf_path=file_input, 
        start_page=6, 
        end_page=20, 
        base_folder='hasil_terjemahan_ai'
    )
