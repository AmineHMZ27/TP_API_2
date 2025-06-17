from django.urls import path
from .views import RePushTransactionView, RePushAllTransactionsView, RePushCheckView, FullTextSearchView, TrainModelView, GrantAccessView, RevokeAccessView, TransactionListView, RePushAllTransactionsView, ListResourcesView, AuditLogListView, MoneySpentLast5Min, TotalSpentPerUserAndType, TopProductsView

urlpatterns = [
    path('permissions/grant/', GrantAccessView.as_view()),
    path('permissions/revoke/', RevokeAccessView.as_view()),
    path('data/', TransactionListView.as_view()),
    path('audit/logs/', AuditLogListView.as_view()),
    path('metrics/spent-last-5min/', MoneySpentLast5Min.as_view()),
    path('metrics/spent-by-user/', TotalSpentPerUserAndType.as_view()),
    path('metrics/top-products/', TopProductsView.as_view()),
    path('search/', FullTextSearchView.as_view()),
    path('train-model/', TrainModelView.as_view()),
    path('repush/check/', RePushCheckView.as_view()),
    path('repush/transaction/', RePushTransactionView.as_view()),
    path('api/repush/all/', RePushAllTransactionsView.as_view(), name='repush_all'),
    path('api/resources/', ListResourcesView.as_view(), name='list_resources'),
]
