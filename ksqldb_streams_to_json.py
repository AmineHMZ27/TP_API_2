import os
import json
import requests
from datetime import datetime

KSQLDB_SERVER = "http://localhost:9021"
STREAMS_JSON_FILE = r"datalake/streams_names/streams.json"
SAVE_DIRECTORY = r"datalake/streams"

if not os.path.isfile(STREAMS_JSON_FILE):
    print(f"[FATAL] Le fichier {STREAMS_JSON_FILE} n'existe pas.")
    exit(1)

def query_ksqldb(ksql_query, is_stream=True):
    endpoint = f"{KSQLDB_SERVER}/query-stream" if is_stream else f"{KSQLDB_SERVER}/query"
    payload = {
        ("sql" if is_stream else "ksql"): ksql_query,
        "properties": {"auto.offset.reset": "earliest"}
    }
    headers = {
        "Content-Type": "application/vnd.ksql.v1+json"
    }
    response = requests.post(endpoint, json=payload, headers=headers, timeout=10, stream=True)
    response.raise_for_status()
    return response.iter_lines()

def load_stream_names(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return [stream["name"] for stream in data.get("streams", [])]

def extract_and_save_stream(stream_name):
    print(f"[INFO] Extracting stream {stream_name}...")

    try:
        query = f"SELECT * FROM {stream_name} EMIT CHANGES LIMIT 100;"
        response_lines = query_ksqldb(query, is_stream=True)

        rows = []
        column_names = []

        for idx, line in enumerate(response_lines):
            if line:
                decoded_line = line.decode('utf-8')
                data = json.loads(decoded_line)
                if idx == 0:
                    column_names = data.get("columnNames", [])
                else:
                    row_dict = dict(zip(column_names, data))
                    rows.append(row_dict)
                if len(rows) >= 100:
                    break

        if not rows:
            print(f"[WARNING] No records for {stream_name}")
            return

        today = datetime.now().strftime("%Y-%m-%d")
        stream_save_dir = os.path.join(SAVE_DIRECTORY, stream_name, today)
        os.makedirs(stream_save_dir, exist_ok=True)
        output_path = os.path.join(stream_save_dir, f"{stream_name}_{today}.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2, ensure_ascii=False)

        print(f"[SUCCESS] Stream {stream_name} saved in {output_path}")

    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTPError for {stream_name}: {str(e)}")
    except Exception as e:
        print(f"[ERROR] Error for {stream_name}: {str(e)}")

if __name__ == "__main__":
    print("[INFO] Starting stream extraction...")

    try:
        stream_names = load_stream_names(STREAMS_JSON_FILE)

        for stream_name in stream_names:
            extract_and_save_stream(stream_name)

        print("[INFO] Extraction completed!")

    except Exception as e:
        print(f"[FATAL] Erreur critique: {str(e)}")
