import requests
import json
import sqlite3
import os
import time
import pandas as pd

def fetch_nemo_data(page_index=0):
    url = "https://www.nemoapp.kr/api/store/search-list"
    params = {
        "Subway": "222",
        "Radius": "1000",
        "CompletedOnly": "false",
        "NELat": "37.513418496475516",
        "NELng": "127.03560698494442",
        "SWLat": "37.48333024902553",
        "SWLng": "127.00058793535545",
        "Zoom": "15",
        "SortBy": "29",
        "PageIndex": page_index
    }
    
    headers = {
        "referer": "https://www.nemoapp.kr/store",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def save_to_sqlite(all_items):
    if not all_items:
        return

    db_path = os.path.join("data", "nemo_data.db")
    # 기존 파일 삭제 후 새로 생성 (전체 수집이므로)
    if os.path.exists(db_path):
        os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    first_item = all_items[0]
    columns = list(first_item.keys())
    
    col_def = ", ".join([f'"{col}" TEXT' for col in columns])
    cursor.execute(f'CREATE TABLE IF NOT EXISTS stores ({col_def})')

    placeholders = ", ".join(["?" for _ in columns])
    insert_sql = f'INSERT INTO stores ({", ".join([f'"{col}"' for col in columns])}) VALUES ({placeholders})'
    
    for item in all_items:
        values = []
        for col in columns:
            val = item.get(col)
            if isinstance(val, (dict, list)):
                values.append(json.dumps(val, ensure_ascii=False))
            else:
                values.append(str(val) if val is not None else None)
        cursor.execute(insert_sql, values)

    conn.commit()
    conn.close()
    print(f"Saved {len(all_items)} items to SQLite: {db_path}")

def save_to_csv(all_items):
    if not all_items:
        return
    csv_path = os.path.join("data", "nemo_data.csv")
    df = pd.DataFrame(all_items)
    # 엑셀에서 한글 안깨지게 utf-8-sig 사용
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"Saved {len(all_items)} items to CSV: {csv_path}")

def main():
    all_items = []
    page_index = 0
    
    print("Starting full data collection...")
    
    while True:
        data = fetch_nemo_data(page_index)
        if not data or "items" not in data or not data["items"]:
            print(f"Finished at page {page_index}. No more data.")
            break
            
        items = data["items"]
        all_items.extend(items)
        print(f"Page {page_index}: Collected {len(items)} items (Total: {len(all_items)})")
        
        page_index += 1
        time.sleep(0.5) # 서버 부하 방지
        
    if all_items:
        save_to_sqlite(all_items)
        save_to_csv(all_items)
        
        # 샘플 JSON 저장
        with open(os.path.join("data", "sample_data.json"), "w", encoding="utf-8") as f:
            json.dump(all_items[0], f, indent=4, ensure_ascii=False)
    else:
        print("No data collected.")

if __name__ == "__main__":
    main()
