from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AuthLoginView,
    AuthLogoutView,
    AuthMeView,
    HealthView,
    DashboardView,
    EntradaEstoqueViewSet,
    EstoqueViewSet,
    MovimentacaoEstoqueViewSet,
    ProdutoCimentoViewSet,
    RelatorioPorClienteView,
    RelatorioPorMarcaView,
    RelatorioResumoView,
    VendaViewSet,
)

router = DefaultRouter()
router.register('produtos', ProdutoCimentoViewSet)
router.register('estoque', EstoqueViewSet, basename='estoque')
router.register('entradas', EntradaEstoqueViewSet, basename='entradas')
router.register('vendas', VendaViewSet, basename='vendas')
router.register('movimentacoes', MovimentacaoEstoqueViewSet, basename='movimentacoes')

urlpatterns = [
	path('health/', HealthView.as_view(), name='health'),
    path('auth/login/', AuthLoginView.as_view(), name='auth-login'),
    path('auth/logout/', AuthLogoutView.as_view(), name='auth-logout'),
    path('auth/me/', AuthMeView.as_view(), name='auth-me'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('relatorios/resumo/', RelatorioResumoView.as_view(), name='relatorio-resumo'),
    path('relatorios/por-cliente/', RelatorioPorClienteView.as_view(), name='relatorio-por-cliente'),
    path('relatorios/por-marca/', RelatorioPorMarcaView.as_view(), name='relatorio-por-marca'),
]

urlpatterns += router.urls
