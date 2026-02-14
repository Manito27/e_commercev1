from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginView
from .views import (
    CategoriaProdutoViewSet,
    ProdutoViewSet,
    FuncionarioViewSet,
    ClienteViewSet,
    VendaViewSet,
    ItemVendaViewSet,
    PagamentoViewSet,
    AdministradorViewSet,
    MeView
)

# Cria o router
router = DefaultRouter()

# Registra os ViewSets
router.register(r'categorias', CategoriaProdutoViewSet, basename='categoriaproduto')
router.register(r'produtos', ProdutoViewSet, basename='produto')
router.register(r'administradores', AdministradorViewSet, basename='administrador')
router.register(r'funcionarios', FuncionarioViewSet, basename='funcionario')
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'vendas', VendaViewSet,basename= 'venda')
router.register(r'pagamentos', PagamentoViewSet, basename='pagamento')

router.register(r'itens-venda', ItemVendaViewSet, basename='itemvenda')


# URLs
urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('', include(router.urls)),
    path('me/', MeView.as_view(), name='me'),

]