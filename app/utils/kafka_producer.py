import json
from kafka import KafkaProducer

def repush_to_kafka(topic, message, bootstrap_servers="localhost:9092"):
    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )
    producer.send(topic, value=message)
    producer.flush()
    producer.close()
