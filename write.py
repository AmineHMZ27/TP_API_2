import os
import json
from kafka import KafkaConsumer
from datetime import datetime
import schedule
import time

KAFKA_TOPIC = 'transaction_log'
KAFKA_BOOTSTRAP = 'localhost:9092'
GROUP_ID = 'datalake'
OUTPUT_DIR = 'datalake/transaction_log'


def wrie(record):
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_path = os.path.join(OUTPUT_DIR, date_str)
    os.makedirs(output_path, exist_ok=True)

    file_path = os.path.join(output_path, 'data.json')
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')


def consume_and_save():
    print(f"[INFO] Starting Kafka consumer at {datetime.now().strftime('%H:%M:%S')}")
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id=GROUP_ID,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    try:
        for message in consumer:
            record = message.value
            print(f"[RECEIVED] {record}")
            wrie(record)
    except KeyboardInterrupt:
        print("[INFO] Interrupted by user.")
    finally:
        consumer.close()
        print("[INFO] Consumer closed.")


if __name__ == "__main__":
    print("[INFO] Starting consumer loop...")
    consume_and_save()
    # If scheduled:
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)