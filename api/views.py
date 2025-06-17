import os
import json
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from .models import FileAccess, AuditLog
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from pathlib import Path
from kafka import KafkaProducer
from ml.train_model import train_model_from_json
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from Project_API.utils.kafka_producer import repush_to_kafka

def log_request(request):
    AuditLog.objects.create(
        user=request.user,
        endpoint=request.path,
        method=request.method,
        query_params=json.dumps(request.query_params.dict()),
        body=json.dumps(request.data) if hasattr(request, 'data') else ''
    )

class TenPerPagePagination(PageNumberPagination):
    page_size = 10

class RePushTransactionView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'transaction_id',
                openapi.IN_QUERY,
                description="Transaction ID to repush",
                type=openapi.TYPE_STRING,
                required=True
            )
        ]
    )

    def get(self, request):
        transaction_id = request.query_params.get("transaction_id")
        if not transaction_id:
            return Response({"error": "transaction_id is required"}, status=400)

        for root, _, files in os.walk("datalake/transaction_log"):
            for file in files:
                if file.endswith(".json"):
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        for line in f:
                            try:
                                data = json.loads(line)
                                if data.get("transaction_id") == transaction_id:
                                    data["timestamp_of_reception_log"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                                    producer = KafkaProducer(
                                        bootstrap_servers="localhost:9092",
                                        value_serializer=lambda v: json.dumps(v).encode("utf-8")
                                    )
                                    producer.send("transaction_log", value=data)
                                    producer.flush()
                                    producer.close()

                                    return Response({"message": "Transaction repushed"}, status=200)
                            except json.JSONDecodeError:
                                continue

        return Response({"error": "Transaction not found"}, status=404)

class RePushAllTransactionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return self._repush_all()

    def post(self, request):
        return self._repush_all()

    def _repush_all(self):
        count = 0
        for root, _, files in os.walk("datalake/transaction_log"):
            for file in files:
                if file.endswith(".json"):
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        for line in f:
                            try:
                                data = json.loads(line)
                                data["timestamp_of_reception_log"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                producer = KafkaProducer(
                                    bootstrap_servers="localhost:9092",
                                    value_serializer=lambda v: json.dumps(v).encode("utf-8")
                                )
                                producer.send("transaction_log", value=data)
                                producer.flush()
                                producer.close()
                                count += 1
                            except Exception:
                                continue
        if count == 0:
            return Response({"message": "No valid transactions found"}, status=404)
        return Response({"message": f"{count} transactions repushed to Kafka"}, status=200)

class ListResourcesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        base_path = os.path.join(settings.BASE_DIR, "datalake")
        resources = []

        for root, _, files in os.walk(base_path):
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, base_path)
                resources.append(relative_path)

        return Response({"resources": resources})


class TransactionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        log_request(request)
        resource = request.query_params.get("resource")
        if not resource:
            return Response({"error": "Missing ?resource="}, status=400)

        has_access = FileAccess.objects.filter(
            user=request.user,
            resource=resource,
            can_read=True
        ).exists()

        if not has_access:
            return Response({"error": "Access denied"}, status=403)

        file_path = os.path.join(settings.BASE_DIR, "datalake", resource)
        if not os.path.isfile(file_path):
            return Response({"error": f"File not found: {resource}"}, status=404)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON format"}, status=500)

        def matches_filters(item):
            for key, value in request.query_params.items():
                if key in ["resource", "fields", "page"]:
                    continue
                if "__" in key:
                    field, op = key.split("__", 1)
                    try:
                        item_val = float(item.get(field, 0))
                        filter_val = float(value)
                    except (TypeError, ValueError):
                        return False
                    if op == "gt" and not (item_val > filter_val): return False
                    if op == "lt" and not (item_val < filter_val): return False
                    if op == "eq" and not (item_val == filter_val): return False
                else:
                    if str(item.get(key)) != value:
                        return False
            return True

        data = [item for item in data if matches_filters(item)]

        fields = request.query_params.get("fields")
        if fields:
            field_list = [f.strip() for f in fields.split(",")]
            data = [{k: v for k, v in item.items() if k in field_list} for item in data]

        paginator = TenPerPagePagination()
        paginated_data = paginator.paginate_queryset(data, request)
        return paginator.get_paginated_response(paginated_data)

class GrantAccessView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        log_request(request)
        username = request.data.get('username')
        resource = request.data.get('resource')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        access, _ = FileAccess.objects.get_or_create(user=user, resource=resource)
        access.can_read = True
        access.save()
        return Response({'message': 'Access granted'}, status=201)

class RevokeAccessView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        log_request(request)
        username = request.data.get('username')
        resource = request.data.get('resource')

        try:
            user = User.objects.get(username=username)
            access = FileAccess.objects.get(user=user, resource=resource)
        except (User.DoesNotExist, FileAccess.DoesNotExist):
            return Response({'error': 'User or permission not found'}, status=404)

        access.delete()
        return Response({'message': 'Access revoked'}, status=200)

class AuditLogListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            return Response({"error": "Forbidden"}, status=403)

        logs = AuditLog.objects.order_by("-timestamp")[:100]
        return Response([
            {
                "user": log.user.username,
                "timestamp": log.timestamp,
                "endpoint": log.endpoint,
                "method": log.method,
                "query_params": log.query_params,
                "body": log.body
            }
            for log in logs
        ])

class MoneySpentLast5Min(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        log_request(request)
        resource = request.query_params.get("resource")
        if not resource:
            return Response({"error": "Missing ?resource="}, status=400)

        file_path = os.path.join(settings.BASE_DIR, "datalake", resource)
        if not os.path.isfile(file_path):
            return Response({"error": "File not found"}, status=404)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=5)
        total = 0
        for tx in data:
            try:
                ts = datetime.fromisoformat(tx.get("timestamp").replace("Z", "+00:00"))
                if ts >= cutoff and tx.get("status") == "completed":
                    total += float(tx.get("amount", 0))
            except Exception:
                continue

        return Response({"total_last_5_minutes": total})

class TotalSpentPerUserAndType(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        log_request(request)
        resource = request.query_params.get("resource")
        if not resource:
            return Response({"error": "Missing ?resource="}, status=400)

        file_path = os.path.join(settings.BASE_DIR, "datalake", resource)
        if not os.path.isfile(file_path):
            return Response({"error": "File not found"}, status=404)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        result = {}
        for tx in data:
            user = tx.get("user_id")
            tx_type = tx.get("transaction_type")
            key = (user, tx_type)
            if None in key:
                continue
            result[key] = result.get(key, 0) + float(tx.get("amount", 0))

        return Response([
            {"user_id": k[0], "transaction_type": k[1], "total_spent": v}
            for k, v in result.items()
        ])

class TopProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        log_request(request)
        resource = request.query_params.get("resource")
        x = request.query_params.get("top", 3)
        try:
            x = int(x)
        except ValueError:
            return Response({"error": "Invalid ?top="}, status=400)

        file_path = os.path.join(settings.BASE_DIR, "datalake", resource)
        if not os.path.isfile(file_path):
            return Response({"error": "File not found"}, status=404)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        counter = {}
        for tx in data:
            product = tx.get("product_id")
            qty = int(tx.get("quantity", 0))
            if product:
                counter[product] = counter.get(product, 0) + qty

        top_items = sorted(counter.items(), key=lambda kv: kv[1], reverse=True)[:x]

        return Response([
            {"product_id": pid, "quantity": qty}
            for pid, qty in top_items
        ])

class FullTextSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        log_request(request)
        search_text = request.query_params.get("q")
        date = request.query_params.get("date")
        if not search_text or not date:
            return Response({"error": "Missing ?q= and/or ?date="}, status=400)

        base_path = Path(settings.BASE_DIR) / "datalake" / "transaction_log" / date
        if not base_path.exists():
            return Response({"error": f"No data for date {date}"}, status=404)

        search_results = []
        matched_resources = []
        for json_file in base_path.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    if self.contains_text(item, search_text):
                        search_results.append(item)
                        matched_resources.append(str(json_file.relative_to(settings.BASE_DIR)))
            except Exception:
                continue

        return Response({
            "query": search_text,
            "resources_matched": list(set(matched_resources)),
            "results": search_results
        })

    def contains_text(self, item, text):
        text = str(text).lower()

        def search_in(value):
            if isinstance(value, dict):
                return any(search_in(v) for v in value.values())
            elif isinstance(value, list):
                return any(search_in(v) for v in value)
            else:
                return text in str(value).lower()

        return search_in(item)

class TrainModelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        log_request(request)
        resource = request.query_params.get("resource")
        if not resource:
            return Response({"error": "Missing ?resource="}, status=400)

        file_path = os.path.join(settings.BASE_DIR, "datalake", resource)
        model_path = os.path.join(settings.BASE_DIR, "ml", "trained_model.pkl")

        if not os.path.isfile(file_path):
            return Response({"error": "File not found"}, status=404)

        try:
            result = train_model_from_json(file_path, model_path)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

        return Response({
            "message": "Model trained successfully",
            "details": result
        })

class RePushCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        log_request(request)
        txn_id = request.query_params.get("id")
        date = request.query_params.get("date")
        topic = request.query_params.get("topic", "transaction_log")
        if not txn_id or not date:
            return Response({"error": "Missing ?id= and/or ?date="}, status=400)

        base_path = os.path.join(settings.BASE_DIR, "datalake", topic, date)
        file_path = os.path.join(base_path, "data.json")

        if not os.path.isfile(file_path):
            return Response({"error": "No data found in lake for given date"}, status=404)

        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                try:
                    data = json.loads(line)
                    if data.get("transaction_id") == txn_id:
                        return Response({
                            "found": True,
                            "transaction": data
                        })
                except:
                    continue

        return Response({"found": False, "message": "Transaction not found"})
