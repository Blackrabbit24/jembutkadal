from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# Input nama pengguna yang ingin divalidasi
nama_input = input("Masukkan nama pelanggan: ")

daftar_nik = []
x = 0
for j in range(20):    
    x += 1
    y = 0    
    for i in range(99):        
        y += 1
        nik = f"3314{x:02d}040799{y:04d}"
        daftar_nik.append(nik)

# Inisialisasi browser Selenium
driver = webdriver.Chrome()  # Pastikan chromedriver terpasang
url_cek_dpt = "https://cekdptonline.kpu.go.id/"
driver.get(url_cek_dpt)

results = []  # inisialisasi list kosong

for nik in daftar_nik:
    time.sleep(1)

    kolom_nik = driver.find_element(By.XPATH, '//input[@type="text"]')
    kolom_nik.clear()
    kolom_nik.send_keys(nik)

    tombol_cari = driver.find_element(By.XPATH, '//button[contains(.,"Pencarian")]')
    tombol_cari.click()
    time.sleep(2)

    try:
        # ambil teks p yang berisi Nama Pemilih
        nama_raw = driver.find_element(By.XPATH, '//p[span[text()="Nama Pemilih"]]').text
        nama_web = nama_raw.replace("Nama Pemilih", "").strip()
        
        if nama_input.lower() == nama_web.lower():
            valid = "COCOK"
            print(f"✅ Ditemukan! NIK: {nik} | Nama: {nama_web}")
            results.append((nik, nama_web, valid))
            print("Halaman web tetap terbuka agar bisa diperiksa.")
            break  # hentikan loop begitu cocok ditemukan
        else:
            valid = "TIDAK COCOK"
            results.append((nik, nama_web, valid))

    except:
        nama_web = "TIDAK DITEMUKAN"
        valid = "TIDAK COCOK"
        results.append((nik, nama_web, valid))

    # Refresh halaman agar siap untuk percobaan berikutnya
    driver.refresh()

driver.quit()

# Opsional: print hasil semua percobaan
for r in results:
    print(r)

