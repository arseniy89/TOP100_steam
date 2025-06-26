import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

os.makedirs("visuals", exist_ok=True)

url = "https://steamcharts.com/top"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')
table = soup.find("table", {"class": "common-table"})
if table is None:
    table = soup.find("table")
    if table is None:
        print("Ничего на странице не найдено.")
        print("Доступные таблицы на странице:")
        tables = soup.find_all("table")
        for i, t in enumerate(tables):
            print(f"Таблица {i}: {t.get('class', 'без класса')}")
        exit()

rows = table.find_all("tr")
header_row = rows[0] if rows else None

if header_row:
    print("Заголовки таблицы:")
    headers = [th.text.strip() for th in header_row.find_all(["th", "td"])]
    print(headers)

data_rows = rows[1:] if len(rows) > 1 else []

if not data_rows:
    print("Ноу дата роус")
    exit()

print(f"Найдено строк данных: {len(data_rows)}")


data = []
for i, row in enumerate(data_rows):
    cols = row.find_all("td")
    if len(cols) < 4:
        print(f"Строка {i+1}: недостаточно колонок ({len(cols)})")
        continue
    if i < 5:
        col_texts = [col.text.strip() for col in cols]
        print(f"Строка {i+1}: {col_texts}")
    try:
        rank_text = cols[0].text.strip().rstrip('.')
        rank = int(rank_text)
        name = cols[1].text.strip()
        current_text = cols[2].text.replace(',', '').replace('-', '0').strip()

        if not current_text or not current_text.replace('.', '').isdigit():
            current_players = 0
        else:
            current_players = int(float(current_text))
        
        peak_today = 0
        if len(cols) > 3:
            peak_text = cols[3].text.replace(',', '').replace('-', '0').strip()
            if peak_text and peak_text.replace('.', '').isdigit():
                peak_today = int(float(peak_text))

        gain = ""
        if len(cols) > 4:
            gain = cols[4].text.strip()
        elif len(cols) > 3 and not peak_text:
            gain = cols[3].text.strip()  
        data.append([rank, name, current_players, peak_today, gain])
        
    except (ValueError, IndexError) as e:
        print(f"Ошибка обработки строки {i+1}: {e}")
        continue

if not data:
    print("Ничего не спарсили")
    print("Разрабы...")
    for i, row in enumerate(data_rows[:5]):
        cols = row.find_all("td")
        print(f"Строка {i+1}: {[col.text.strip() for col in cols]}")
    exit()

df = pd.DataFrame(data, columns=["Rank", "Game", "Current", "Peak", "Gain"])
df["Current"] = df["Current"].astype(int)
df["Peak"] = df["Peak"].astype(int)
df.to_csv("steam_top_100.csv", index=False)

print(f"Успешно удалось спарсить {len(df)} игр")
print(df.head(10))
print(f"Топ игра: {df.iloc[0]['Game']} с {df.iloc[0]['Current']:,} игроков")

if len(df) < 50:
    print(f"\n Получено только {len(df)} игр из ожидаемых 100.")
    print("Возможные причины:")
    print("1. Сайт использует JavaScript для загрузки данных")
    print("2. Изменилась структура HTML")
    print("3. Блокировка по User-Agent")

top10 = df.sort_values("Current", ascending=False).head(10)

plt.figure(figsize=(12,6))
sns.barplot(data=top10, x="Current", y="Game", hue="Game", palette="rocket", legend=False)
plt.title("Топ-10 игр по текущему онлайну в Steam")
plt.xlabel("Текущий онлайн")
plt.ylabel("Игра")
plt.tight_layout()
plt.savefig("visuals/top10_current.png", dpi=300, bbox_inches='tight')
plt.show()

if df["Peak"].sum() > 0:
    df["Surge Ratio"] = df["Peak"] / df["Current"].replace(0, 1)  # Избегаем деления на 0
    surge = df[df["Peak"] > 0].sort_values("Surge Ratio", ascending=False).head(10)
    
    if len(surge) > 0:
        plt.figure(figsize=(12,6))
        sns.barplot(data=surge, x="Surge Ratio", y="Game", hue="Game", palette="mako", legend=False)
        plt.title("Игры с самым высоким скачком онлайна за сегодня")
        plt.xlabel("Peak / Current Ratio")
        plt.tight_layout()
        plt.savefig("visuals/peak_surges.png", dpi=300, bbox_inches='tight')
        plt.show()
else:
    print("Данные о пиковом онлайне отсутствуют")

plt.figure(figsize=(12,6))
top20 = df.head(20)
plt.bar(range(len(top20)), top20["Current"], color='steelblue')
plt.xticks(range(len(top20)), [name[:15] + '...' if len(name) > 15 else name for name in top20["Game"]], rotation=45, ha='right')
plt.title("Топ-20 игр Steam по онлайну")
plt.ylabel("Текущий онлайн")
plt.tight_layout()
plt.savefig("visuals/top20_distribution.png", dpi=300, bbox_inches='tight')
plt.show()
