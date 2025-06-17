import os
import json
import requests
from datetime import datetime


KSQLDB_SERVER = "http://localhost:8088"
TABLES_JSON_PATH = r"datalake/tables_names/tables.json"
SAVE_DIRECTORY = r"datalake/tables"


def query_ksqldb(ksql_query, is_table=True):
    endpoint = f"{KSQLDB_SERVER}/query" if is_table else f"{KSQLDB_SERVER}/query-stream"
    payload = {
        ("ksql" if is_table else "sql"): ksql_query,
        "properties": {}
    }
    headers = {
        "Content-Type": "application/vnd.ksql.v1+json"
    }
    response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text


def load_table_names(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        table_names = [table["name"] for table in data.get("tables", [])]
    return table_names


def extract_and_save_table(table_name):
    print(f"[INFO] Extracting table {table_name}...")

    try:
        query = f"SELECT * FROM {table_name};"
        response_text = query_ksqldb(query, is_table=True)

        data_lines = response_text.splitlines()

        if not data_lines:
            print(f"[WARNING] No data received for {table_name}")
            return

        metadata = json.loads(data_lines[0])
        column_names = metadata.get("columnNames", [])

        rows = []
        for line in data_lines[1:]:
            if line.strip():
                row_data = json.loads(line)
                row_dict = dict(zip(column_names, row_data))
                rows.append(row_dict)

        if not rows:
            print(f"[WARNING] No records for {table_name}")
            return

        today = datetime.now().strftime("%Y-%m-%d")
        table_save_dir = os.path.join(SAVE_DIRECTORY, table_name, today)
        os.makedirs(table_save_dir, exist_ok=True)
        output_path = os.path.join(table_save_dir, f"{table_name}_{today}.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2, ensure_ascii=False)

        print(f"[SUCCESS] Table {table_name} saved in {output_path}")

    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTPError for {table_name}: {str(e)}")
    except Exception as e:
        print(f"[ERROR] Error for {table_name}: {str(e)}")


if __name__ == "__main__":
    print("[INFO] Starting table extraction...")

    try:
        table_names = load_table_names(TABLES_JSON_PATH)

        for table_name in table_names:
            extract_and_save_table(table_name)

        print("[INFO] Extraction completed!")

    except Exception as e:
        print(f"[FATAL] Erreur critique: {str(e)}")
