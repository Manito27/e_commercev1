from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import login as django_login
from rest_framework.authtoken.serializers import AuthTokenSerializer  # ImportaÃ§Ã£o necessÃ¡ria
from rest_framework import permissions

from rest_framework import viewsets


from django.db.models import Sum

from knox.views import LoginView as KnoxLoginView
from knox.models import AuthToken

from rest_framework.views import APIView


from .models import (
    CategoriaProduto, Produto,
    Funcionario, Cliente, Venda, ItemVenda, Pagamento,Administrador
)
from .serializers import (
    CategoriaProdutoSerializer,
    ProdutoSerializer, ProdutoListSerializer,
    FuncionarioSerializer, FuncionarioCreateSerializer,
    ClienteSerializer, ClienteListSerializer,
    VendaSerializer, ItemVenda,
    ItemVendaSerializer,
    PagamentoSerializer,AdministradorCreateSerializer,AdministradorSerializer
)


# =========================
# Login
# =========================

class LoginView(KnoxLoginView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        django_login(request, user)       
        user_type = None
        redirect_url = None
        
        if Funcionario.objects.filter(user=user).exists():
            user_type = "funcionario"
            redirect_url = "/funcionario/"
        elif Administrador.objects.filter(user=user).exists():
            user_type = "administrador"
            redirect_url = "/administrador/"
        else:
            return Response({'error': 'User type not found'}, status=status.HTTP_400_BAD_REQUEST)
        _, token = AuthToken.objects.create(user)
        print(token)
        return Response({
            "username": user.username,
            "email": user.email,
            "token":token,
            'url':redirect_url
        })



class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        })
# =========================
# PRODUTOS VIEWSETS
# =========================


class CategoriaProdutoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar categorias de produtos
    """
    queryset = CategoriaProduto.objects.all()
    serializer_class = CategoriaProdutoSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        nome = self.request.query_params.get('nome', None)
        
        if nome:
            queryset = queryset.filter(nome__icontains=nome)
        
        return queryset.order_by('nome')
        return Response(resultado)


class ProdutoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar produtos
    """
    queryset = Produto.objects.select_related('categoria', ).all()
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProdutoListSerializer
        return ProdutoSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros
        nome = self.request.query_params.get('nome', None)
        codigo = self.request.query_params.get('codigo_barras', None)
        categoria = self.request.query_params.get('categoria', None)
        estoque_minimo = self.request.query_params.get('estoque_minimo', None)
        
        if nome:
            queryset = queryset.filter(nome__icontains=nome)
        if codigo:
            queryset = queryset.filter(codigo_barras=codigo)
        if categoria:
            queryset = queryset.filter(categoria_id=categoria)
        if estoque_minimo:
            queryset = queryset.filter(estoque__lte=estoque_minimo)
        
        return queryset.order_by('nome')
    
    @action(detail=False, methods=['get'])
    def estoque_baixo(self, request):
        """Retorna produtos com estoque baixo (<=10)"""
        produtos = self.get_queryset().filter(estoque__lte=10)
        serializer = self.get_serializer(produtos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def ajustar_estoque(self, request, pk=None):
        """Ajusta o estoque de um produto"""
        produto = self.get_object()
        quantidade = request.data.get('quantidade')
        operacao = request.data.get('operacao', 'adicionar')  # adicionar ou remover
        
        if quantidade is None:
            return Response(
                {'erro': 'Quantidade nÃ£o fornecida'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            quantidade = int(quantidade)
        except ValueError:
            return Response(
                {'erro': 'Quantidade deve ser um nÃºmero inteiro'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if operacao == 'adicionar':
            produto.estoque += quantidade
        elif operacao == 'remover':
            if produto.estoque < quantidade:
                return Response(
                    {'erro': 'Estoque insuficiente'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            produto.estoque -= quantidade
        else:
            return Response(
                {'erro': 'OperaÃ§Ã£o invÃ¡lida. Use "adicionar" ou "remover"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        produto.save()
        serializer = self.get_serializer(produto)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def buscar_por_codigo(self, request):
        """Busca produto por cÃ³digo de barras"""
        codigo = request.query_params.get('codigo', None)
        
        if not codigo:
            return Response(
                {'erro': 'CÃ³digo de barras nÃ£o fornecido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            produto = Produto.objects.get(codigo_barras=codigo)
            serializer = self.get_serializer(produto)
            return Response(serializer.data)
        except Produto.DoesNotExist:
            return Response(
                {'erro': 'Produto nÃ£o encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

# =========================
# Admin VIEWSET
# =========================

class AdministradorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar funcionÃ¡rios
    """
    queryset = Administrador.objects.select_related('user').all()
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AdministradorCreateSerializer
        return AdministradorSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros
        nome = self.request.query_params.get('nome', None)
        cargo = self.request.query_params.get('cargo', None)
        
        if nome:
            queryset = queryset.filter(
                Q(nome__icontains=nome) | Q(apelido__icontains=nome)
            )
        if cargo:
            queryset = queryset.filter(cargo__icontains=cargo)
        
        return queryset.order_by('nome')
    
    @action(detail=True, methods=['get'])
    def vendas(self, request, pk=None):
        """Retorna vendas de um administrador"""
        administrador = self.get_object()
        data_inicio = request.query_params.get('data_inicio', None)
        data_fim = request.query_params.get('data_fim', None)

        vendas = Venda.objects.filter(user=administrador.user).select_related('cliente').prefetch_related('itens', 'pagamentos')

        if data_inicio:
            vendas = vendas.filter(data_venda__gte=data_inicio)
        if data_fim:
            vendas = vendas.filter(data_venda__lte=data_fim)

        total_vendas = vendas.aggregate(
            total=Sum('total'),
            quantidade=Count('id')
        )

        return Response({
            'administrador': AdministradorSerializer(administrador).data,
            'total_vendido': total_vendas['total'] or 0,
            'quantidade_vendas': total_vendas['quantidade'] or 0,
            'vendas': VendaSerializer(vendas.order_by('-data_venda'), many=True).data
        })

# =========================
# FUNCIONÃRIO VIEWSET
# =========================

class FuncionarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar funcionÃ¡rios
    """
    queryset = Funcionario.objects.select_related('user').all()
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return FuncionarioCreateSerializer
        return FuncionarioSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros
        nome = self.request.query_params.get('nome', None)
        cargo = self.request.query_params.get('cargo', None)
        
        if nome:
            queryset = queryset.filter(
                Q(nome__icontains=nome) | Q(apelido__icontains=nome)
            )
        if cargo:
            queryset = queryset.filter(cargo__icontains=cargo)
        
        return queryset.order_by('nome')
    
    @action(detail=True, methods=['get'])
    def vendas(self, request, pk=None):
        """Retorna vendas de um funcionario"""
        funcionario = self.get_object()
        data_inicio = request.query_params.get('data_inicio', None)
        data_fim = request.query_params.get('data_fim', None)

        vendas = Venda.objects.filter(user=funcionario.user).select_related('cliente').prefetch_related('itens', 'pagamentos')

        if data_inicio:
            vendas = vendas.filter(data_venda__gte=data_inicio)
        if data_fim:
            vendas = vendas.filter(data_venda__lte=data_fim)

        total_vendas = vendas.aggregate(
            total=Sum('total'),
            quantidade=Count('id')
        )

        return Response({
            'funcionario': FuncionarioSerializer(funcionario).data,
            'total_vendido': total_vendas['total'] or 0,
            'quantidade_vendas': total_vendas['quantidade'] or 0,
            'vendas': VendaSerializer(vendas.order_by('-data_venda'), many=True).data
        })

# =========================
# CLIENTE VIEWSET
# =========================

class ClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar clientes
    """
    queryset = Cliente.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ClienteListSerializer
        return ClienteSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros
        nome = self.request.query_params.get('nome', None)
        contacto = self.request.query_params.get('contacto', None)
        documento = self.request.query_params.get('documento', None)
        
        if nome:
            queryset = queryset.filter(
                Q(nome__icontains=nome) | Q(apelido__icontains=nome)
            )
        if contacto:
            queryset = queryset.filter(contacto__icontains=contacto)
        if documento:
            queryset = queryset.filter(numero_documento=documento)
        
        return queryset.order_by('nome')
    
    @action(detail=True, methods=['get'])
    def historico_compras(self, request, pk=None):
        """Retorna histÃ³rico de compras de um cliente"""
        cliente = self.get_object()
        
        faturas = Fatura.objects.filter(cliente=cliente).order_by('-data_venda')
        
        total_gasto = faturas.aggregate(total=Sum('valor_total'))
        
        return Response({
            'cliente': ClienteSerializer(cliente).data,
            'total_gasto': total_gasto['total'] or 0,
            'quantidade_compras': faturas.count(),
            'compras': FaturaListSerializer(faturas[:10], many=True).data  # Ãšltimas 10
        })
    
    @action(detail=False, methods=['get'])
    def top_clientes(self, request):
        """Retorna os top clientes por valor gasto"""
        limit = int(request.query_params.get('limit', 10))
        
        clientes = Cliente.objects.annotate(
            total_gasto=Sum('fatura__valor_total'),
            total_compras=Count('fatura')
        ).filter(total_gasto__isnull=False).order_by('-total_gasto')[:limit]
        
        resultado = []
        for cliente in clientes:
            resultado.append({
                'cliente': ClienteSerializer(cliente).data,
                'total_gasto': cliente.total_gasto,
                'total_compras': cliente.total_compras
            })
        
        return Response(resultado)


# =========================
# FATURA VIEWSET
# =========================

class VendaViewSet(viewsets.ModelViewSet):

    queryset = Venda.objects.select_related('cliente').prefetch_related('itens', 'pagamentos')
    serializer_class = VendaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        cliente = self.request.query_params.get('cliente', None)
        status_venda = self.request.query_params.get('status', None)

        if cliente:
            queryset = queryset.filter(cliente_id=cliente)
        if status_venda:
            queryset = queryset.filter(status=status_venda)

        return queryset.order_by('-data_venda')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def adicionar_item(self, request, pk=None):

        venda = self.get_object()

        serializer = ItemVendaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(venda=venda)

        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def total_pago(self, request, pk=None):
        venda = self.get_object()

        total_pago = venda.pagamentos.aggregate(
            total=Sum('valor')
        )['total'] or 0

        return Response({
            "total_venda": venda.total,
            "total_pago": total_pago,
            "status": venda.status
        })


# =========================
# ITEM VENDA VIEWSET
# =========================

class ItemVendaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet apenas leitura para itens de venda
    (CriaÃ§Ã£o/ediÃ§Ã£o feita via FaturaViewSet)
    """
    queryset = ItemVenda.objects.select_related('fatura', 'produto').all()
    serializer_class = ItemVendaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        fatura = self.request.query_params.get('fatura', None)
        produto = self.request.query_params.get('produto', None)
        
        if fatura:
            queryset = queryset.filter(fatura_id=fatura)
        if produto:
            queryset = queryset.filter(produto_id=produto)
        
        return queryset.order_by('-fatura__data_venda')


# =========================
# PAGAMENTO VIEWSET
# =========================
class PagamentoViewSet(viewsets.ModelViewSet):
    queryset = Pagamento.objects.all()
    serializer_class = PagamentoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

