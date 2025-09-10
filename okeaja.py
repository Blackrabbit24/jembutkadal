from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# Input nama pengguna yang ingin divalidasi
nama_input = input("Masukkan nama pelanggan: ")

# Baca daftar NIK dari file txt
# with open("worldlist.txt", "r") as file:
#     daftar_nik = [line.strip() for line in file.readlines()]

daftar_nik = []   # inisialisasi list kosong

x = 0
for j in range(99):    
    x += 1
    y = 0    
    for i in range(9999):        
        y += 1
        nik = f"3314{x:02d}040799{y:04d}"
        daftar_nik.append(nik)   # simpan ke list


# Inisialisasi browser Selenium
driver = webdriver.Chrome()  # Pastikan chromedriver terpasang

url_cek_dpt = "https://cekdptonline.kpu.go.id/"  # Ganti dengan URL sebenarnya
driver.get(url_cek_dpt)

results = []

for nik in daftar_nik:
    time.sleep(1)  # Tunggu load halaman, bisa dioptimalkan

    # Temukan kolom input NIK (sesuaikan By dan value sesuai struktur web)
    kolom_nik = driver.find_element(By.XPATH, '//input[@type="text"]')
    kolom_nik.clear()
    kolom_nik.send_keys(nik)

    # Klik tombol pencarian (sesuaikan dengan XPATH / Selector yang benar)
    tombol_cari = driver.find_element(By.XPATH, '//button[contains(.,"Pencarian")]')
    tombol_cari.click()
    time.sleep(2)  # Tunggu hasil pencarian

    # Ambil nama dari hasil pencarian (ubah sesuai XPATH hasil sebenarnya)
    try:
        nama_web = driver.find_element(By.XPATH, '//div[contains(@class,"nama-pemilih")]').text
        valid = "COCOK" if nama_input.lower() == nama_web.lower() else "TIDAK COCOK"
    except:
        nama_web = "TIDAK DITEMUKAN"
        valid = "TIDAK COCOK"

    results.append((nik, nama_web, valid))

    # Refresh halaman, atau klik tombol 'F5' jika diperlukan
    driver.refresh()

# Cetak/ekspor hasil validasi
for nik, hasil_nama, status in results:
    print(f"NIK: {nik} | Nama: {hasil_nama} | Status: {status}")

driver.quit()
