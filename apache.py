import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import schedule
import time
import os
import json
from datetime import datetime

DATALAKE_FOLDER = r"C:\Users\eleah\TP3\datalake\streams"

def process_stream_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_pipeline():
    print(f"[INFO] Running Beam pipeline at {datetime.now()}")

    today = datetime.now().strftime('%Y-%m-%d')
    stream_folder = os.path.join(DATALAKE_FOLDER, 'transactions_transformed', today)

    if not os.path.exists(stream_folder):
        print(f"[WARNING] No data for {today}")
        return

    with beam.Pipeline(options=PipelineOptions()) as p:
        (
            p
            | 'Create list of files' >> beam.Create([os.path.join(stream_folder, f) for f in os.listdir(stream_folder) if f.endswith(".json")])
            | 'Read and parse JSON' >> beam.FlatMap(lambda path: process_stream_file(path))
            | 'Print records' >> beam.Map(print)
        )

schedule.every(10).minutes.do(run_pipeline)

if __name__ == "__main__":
    print("[INFO] Starting orchestration loop...")
    run_pipeline()
    while True:
        schedule.run_pending()
        time.sleep(1)
