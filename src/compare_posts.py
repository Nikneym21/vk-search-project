import csv
from pathlib import Path

# Пути к файлам
ETALON_CSV = '168_24.07_18.04_25.07.2025.csv'
RESULT_CSV = 'data/results/search_20250726_010716.csv'

# --- 1. Собираем все ссылки и тексты из эталона ---
print(f"Чтение эталона: {ETALON_CSV}")
eth_links = set()
eth_texts = dict()  # link -> text
with open(ETALON_CSV, encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        link = row['Ссылка'].strip()
        text = row['Текст'].strip()
        eth_links.add(link)
        eth_texts[link] = text
print(f"В эталоне ссылок: {len(eth_links)}")

# --- 2. Собираем все ссылки и тексты из результата (батчами) ---
print(f"Чтение результата: {RESULT_CSV}")
res_links = set()
res_texts = dict()  # link -> text
batch_size = 10000
row_count = 0
with open(RESULT_CSV, encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        owner_id = row.get('owner_id') or row.get('from_id')
        post_id = row.get('id')
        if not owner_id or not post_id:
            continue
        link = f"https://vk.com/wall{owner_id}_{post_id}"
        text = row.get('text', '').strip()
        res_links.add(link)
        res_texts[link] = text
        row_count += 1
        if row_count % batch_size == 0:
            print(f"  ...прочитано {row_count} строк")
print(f"В результате ссылок: {len(res_links)}")

# --- 3. Сравнение по ссылке ---
common_links = eth_links & res_links
only_in_ethalon = eth_links - res_links
only_in_result = res_links - eth_links
print(f"\nСовпадающих ссылок: {len(common_links)}")
print(f"Только в эталоне: {len(only_in_ethalon)}")
print(f"Только в результате: {len(only_in_result)}")

# --- 4. Сравнение по тексту для совпадающих ссылок ---
diff_text = []
for link in common_links:
    t1 = eth_texts.get(link, '').strip()
    t2 = res_texts.get(link, '').strip()
    if t1 != t2:
        diff_text.append((link, t1, t2))
print(f"\nИз совпадающих ссылок различие по тексту: {len(diff_text)}")
if diff_text:
    print("Примеры различий по тексту:")
    for link, t1, t2 in diff_text[:10]:
        print(f"- {link}\n  Эталон: {t1}\n  Результат: {t2}\n")

# --- 5. (Опционально) Сохраняем списки различий в файлы ---
Path('compare_out').mkdir(exist_ok=True)
with open('compare_out/only_in_ethalon.txt', 'w', encoding='utf-8') as f:
    for link in only_in_ethalon:
        f.write(link + '\n')
with open('compare_out/only_in_result.txt', 'w', encoding='utf-8') as f:
    for link in only_in_result:
        f.write(link + '\n')
with open('compare_out/diff_text.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Ссылка', 'Текст эталон', 'Текст результат'])
    for link, t1, t2 in diff_text:
        writer.writerow([link, t1, t2])

print("\nСравнение завершено. Подробности в папке compare_out/") 