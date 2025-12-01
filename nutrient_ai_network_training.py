import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

input_file = "products.tsv"
output_file = "kbju_output.xlsx"
error_log_file = "kbju_errors.log"

df = pd.read_csv(input_file, sep="\t")

results = []
errors = []

def clean_value(value, max_value):
    try:
        value = float(value)
        if value < 0 or value > max_value:
            return 0
        return value
    except:
        return 0

def process_url(url):
    url = str(url).strip()
    try:
        if "/product/" not in url:
            return None, url

        barcode = url.split("/product/")[1].split("/")[0]
        json_url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"

        response = requests.get(json_url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get('status') == 1:
            product = data['product']
            name = product.get('product_name', '')
            nutriments = product.get('nutriments', {})

            # Энергия: сначала kcal, иначе конвертируем kJ
            if 'energy-kcal_100g' in nutriments:
                energy = clean_value(nutriments.get('energy-kcal_100g', 0), 1500)
            else:
                energy_kj = clean_value(nutriments.get('energy_100g', 0), 1500)
                energy = round(energy_kj / 4.184, 2)

            protein = clean_value(nutriments.get('proteins_100g', 0), 100)
            fat = clean_value(nutriments.get('fat_100g', 0), 100)
            carb = clean_value(nutriments.get('carbohydrates_100g', 0), 100)

            return [name, energy, protein, fat, carb, url], None
        else:
            return None, url
    except Exception:
        return None, url

# Количество потоков
max_threads = 10
columns = ['Name', 'Energy', 'Protein', 'Fat', 'Carb', 'URL']

# ----------------------------------------
# 🟩 Новый функционал: резюмирование работы
# ----------------------------------------

already_processed = set()

if os.path.exists(output_file):
    try:
        df_done = pd.read_excel(output_file)
        if 'URL' in df_done:
            already_processed = set(df_done['URL'].astype(str))
            print(f"Найдено уже обработанных ссылок: {len(already_processed)}")
    except Exception as e:
        print("Не удалось прочитать существующий XLSX:", e)

# Фильтруем входной файл
df['url'] = df['url'].astype(str)
df_to_process = df[~df['url'].isin(already_processed)]

print(f"Всего ссылок во входном файле: {len(df)}")
print(f"Осталось обработать: {len(df_to_process)}")

# Начальный count включает уже сделанные
count = len(already_processed)

# Создаем пустой Excel-файл, если его нет
if not os.path.exists(output_file):
    pd.DataFrame(columns=columns).to_excel(output_file, index=False)

# ----------------------------------------
# Основная обработка
# ----------------------------------------

with ThreadPoolExecutor(max_threads) as executor:
    future_to_url = {
        executor.submit(process_url, row['url']): row['url']
        for _, row in df_to_process.iterrows()
    }

    for future in as_completed(future_to_url):
        try:
            result, error = future.result()
        except Exception:
            error = future_to_url[future]
            result = None

        count += 1

        if result:
            results.append(result)
        if error:
            errors.append(error)

        # Сохраняем каждые 100 новых обработанных ссылок
        if count % 100 == 0 and results:
            df_chunk = pd.DataFrame(results, columns=columns)
            with pd.ExcelWriter(output_file, mode='a', if_sheet_exists='overlay', engine='openpyxl') as writer:
                startrow = writer.sheets['Sheet1'].max_row if 'Sheet1' in writer.sheets else 0
                df_chunk.to_excel(writer, index=False, header=False, startrow=startrow)

            results = []
            print(f"Сохранил {count} обработанных ссылок (включая старые)")

# Финальное сохранение
if results:
    df_chunk = pd.DataFrame(results, columns=columns)
    with pd.ExcelWriter(output_file, mode='a', if_sheet_exists='overlay', engine='openpyxl') as writer:
        startrow = writer.sheets['Sheet1'].max_row if 'Sheet1' in writer.sheets else 0
        df_chunk.to_excel(writer, index=False, header=False, startrow=startrow)

# Логируем ошибки
with open(error_log_file, "w", encoding="utf-8") as f:
    for e in errors:
        f.write(f"{e}\n")

print("Готово! XLSX и лог ошибок сохранены.")
