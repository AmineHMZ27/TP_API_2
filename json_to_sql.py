import os
import mysql.connector
import json

datalake_path = r'C:\Users\eleah\TP3\datalake\transaction_log'

def find_json_files(directory):
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith(".json"):
                yield os.path.join(dirpath, filename)

def connect_to_mysql():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='1234',
        database='data_warehouse'
    )

def insert_transaction_data(cursor, data):
    sql = """
    INSERT INTO transactions (
        transaction_id,
        user_id,
        user_name,
        product_id,
        amount,
        currency,
        transaction_type,
        status,
        city,
        country,
        payment_method,
        product_category,
        quantity,
        street,
        zip,
        customer_rating,
        discount_code,
        tax_amount,
        thread,
        message_number,
        timestamp_of_reception_log,
        timestamp
    ) VALUES (
        %(transaction_id)s,
        %(user_id)s,
        %(user_name)s,
        %(product_id)s,
        %(amount)s,
        %(currency)s,
        %(transaction_type)s,
        %(status)s,
        %(city)s,
        %(country)s,
        %(payment_method)s,
        %(product_category)s,
        %(quantity)s,
        %(street)s,
        %(zip)s,
        %(customer_rating)s,
        %(discount_code)s,
        %(tax_amount)s,
        %(thread)s,
        %(message_number)s,
        %(timestamp_of_reception_log)s,
        %(timestamp)s
    )
    """
    cursor.execute(sql, data)

def process_json_files():
    connection = connect_to_mysql()
    cursor = connection.cursor()

    date_folders = [folder for folder in os.listdir(datalake_path) if os.path.isdir(os.path.join(datalake_path, folder))]

    print(f"Found date folders: {date_folders}")

    for date_folder in date_folders:
        date_folder_path = os.path.join(datalake_path, date_folder)
        print(f"Processing folder: {date_folder_path}")

        json_files = list(find_json_files(date_folder_path))

        for file_path in json_files:
            print(f"Processing file: {file_path}")

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

                try:
                    messages = json.loads(content)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON file {file_path}. Attempting to parse line-by-line.")
                    messages = []
                    for line in content.splitlines():
                        if line.strip():
                            try:
                                messages.append(json.loads(line))
                            except json.JSONDecodeError as e:
                                print(f"Skipping line: {line} - {e}")

                for message in messages:
                    try:
                        timestamp = message.get('timestamp')
                        if timestamp:
                            timestamp = timestamp.replace('T', ' ').split('.')[0]
                        else:
                            timestamp = None

                        data = {
                            'transaction_id': message.get('transaction_id'),
                            'user_id': message.get('user_id'),
                            'user_name': message.get('user_name'),
                            'product_id': message.get('product_id'),
                            'amount': message.get('amount'),
                            'currency': message.get('currency'),
                            'transaction_type': message.get('transaction_type'),
                            'status': message.get('status'),
                            'city': message.get('location', {}).get('city'),
                            'country': message.get('location', {}).get('country'),
                            'payment_method': message.get('payment_method'),
                            'product_category': message.get('product_category'),
                            'quantity': message.get('quantity'),
                            'street': message.get('shipping_address', {}).get('street'),
                            'zip': message.get('shipping_address', {}).get('zip'),
                            'customer_rating': message.get('customer_rating'),
                            'discount_code': message.get('discount_code'),
                            'tax_amount': message.get('tax_amount'),
                            'thread': message.get('thread'),
                            'message_number': message.get('message_number'),
                            'timestamp_of_reception_log': message.get('timestamp_of_reception_log'),
                            'timestamp': timestamp
                        }

                        insert_transaction_data(cursor, data)
                        connection.commit()
                    except mysql.connector.errors.IntegrityError as e:
                        print(f"[WARNING] Duplicate ignored : {e}")
                    except Exception as e:
                        print(f"[ERROR] Error during insertion : {e}")

    cursor.close()
    connection.close()
    print("Processing completed.")

if __name__ == "__main__":
    process_json_files()
