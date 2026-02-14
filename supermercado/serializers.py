from rest_framework import serializers
from .models import (
    CategoriaProduto, Produto,
    Funcionario, Cliente, Venda, ItemVenda, Pagamento,Administrador
)
from django.contrib.auth.models import User
from django.db.models import Sum
from decimal import Decimal



# =========================
# PRODUTOS SERIALIZERS
# =========================




class CategoriaProdutoSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = CategoriaProduto
        fields = ['id', 'nome']
        


class ProdutoSerializer(serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    
    class Meta:
        model = Produto
        fields = [
            'id', 'nome', 'codigo_barras', 'preco', 
            'estoque', 'categoria', 'categoria_nome','descricao','foto'
        ]
        
    def validate_preco(self, value):
        if value <= 0:
            raise serializers.ValidationError("O preço deve ser maior que zero.")
        return value
    
    def validate_estoque(self, value):
        if value < 0:
            raise serializers.ValidationError("O estoque não pode ser negativo.")
        return value


class ProdutoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagens"""
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    
    class Meta:
        model = Produto
        fields = ['id', 'nome', 'codigo_barras', 'preco', 'estoque', 'categoria', 'categoria_nome', 'descricao', 'foto']


# =========================
# USER SERIALIZERS


class FuncionarioSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    nome_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = Funcionario
        fields = [
            'id', 'user', 'username', 'nome', 'apelido', 
            'nome_completo', 'numero_documento', 'email', 'cargo'
        ]
        read_only_fields = ['id']
    
    def get_nome_completo(self, obj):
        return f"{obj.nome} {obj.apelido}"


class FuncionarioCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar funcionário com usuário"""
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    class Meta:
        model = Funcionario
        fields = [
            'username', 'password', 'nome', 'apelido',
            'numero_documento', 'email', 'cargo'
        ]
    
    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        
        # Cria o usuário
        user = User.objects.create_user(
            username=username,
            password=password,
            email=validated_data.get('email', '')
        )
        
        # Cria o funcionário
        funcionario = Funcionario.objects.create(user=user, **validated_data)
        return funcionario


# =========================
# Admini SERIALIZERS
# =========================

class AdministradorSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    nome_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = Administrador
        fields = [
            'id', 'user', 'username', 'nome', 'apelido', 
            'nome_completo', 'numero_documento', 'email', 'cargo'
        ]
        read_only_fields = ['id']
    
    def get_nome_completo(self, obj):
        return f"{obj.nome} {obj.apelido}"


class AdministradorCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar funcionário com usuário"""
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    class Meta:
        model = Administrador
        fields = [
            'username', 'password', 'nome', 'apelido',
            'numero_documento', 'email', 'cargo'
        ]
    
    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        
        # Cria o usuário
        user = User.objects.create_user(
            username=username,
            password=password,
            email=validated_data.get('email', '')
        )
        
        # Cria o funcionário
        administrador = Administrador.objects.create(user=user, **validated_data)
        return administrador



# =========================
# CLIENTE SERIALIZERS
# =========================

from rest_framework import serializers
from .models import Cliente

class ClienteSerializer(serializers.ModelSerializer):
    tipo_documento_display = serializers.CharField(
        source='get_tipo_documento_display', 
        read_only=True
    )
    
    class Meta:
        model = Cliente
        fields = [
            'id',
            'nome',
            'contacto',
            'tipo_documento',
            'tipo_documento_display',
            'numero_documento',
            'morada',
        ]
        read_only_fields = ['id']

    def validate_contacto(self, value):
        if value and not value.replace('+', '').replace(' ', '').isdigit():
            raise serializers.ValidationError("Contacto inválido.")
        return value


class ClienteListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagens"""
    
    class Meta:
        model = Cliente
        fields = ['id', 'nome', 'contacto', 'tipo_documento', 'numero_documento','morada',]


# =========================
# ITEM VENDA SERIALIZER
# =========================
class ItemVendaSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)

    class Meta:
        model = ItemVenda
        fields = '__all__'
        read_only_fields = ('subtotal', 'venda')



# =========================
# FATURA SERIALIZERS
# =========================
class PagamentoResumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pagamento
        fields = ('id', 'valor', 'metodo', 'valor_recebido', 'troco', 'data_pagamento')


class VendaSerializer(serializers.ModelSerializer):
    itens = ItemVendaSerializer(many=True, read_only=True)
    pagamentos = PagamentoResumoSerializer(many=True, read_only=True)
    vendedor_username = serializers.CharField(source='user.username', read_only=True)
    vendedor_nome = serializers.SerializerMethodField()

    def get_vendedor_nome(self, obj):
        nome = obj.user.get_full_name() if obj.user else ''
        return nome or (obj.user.username if obj.user else None)

    class Meta:
        model = Venda
        fields = '__all__'
        read_only_fields = ('user', 'total', 'status')



# =========================
# PAGAMENTO SERIALIZERS
# =========================
class PagamentoSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        venda = attrs.get('venda') or getattr(self.instance, 'venda', None)
        valor = attrs.get('valor', getattr(self.instance, 'valor', None))
        metodo = attrs.get('metodo', getattr(self.instance, 'metodo', None))
        valor_recebido = attrs.get('valor_recebido', getattr(self.instance, 'valor_recebido', None))

        if venda is None:
            raise serializers.ValidationError({'venda': 'Venda obrigatoria.'})

        if valor is None or valor <= 0:
            raise serializers.ValidationError({'valor': 'O valor do pagamento deve ser maior que zero.'})

        if venda.status == 'CANCELADA':
            raise serializers.ValidationError({'venda': 'Nao e permitido registrar pagamento para venda cancelada.'})

        total_pago = venda.pagamentos.aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        if self.instance is not None:
            total_pago -= self.instance.valor

        restante = (venda.total or Decimal('0.00')) - total_pago
        if restante <= 0:
            raise serializers.ValidationError({'valor': 'Esta venda ja esta totalmente paga.'})

        if valor > restante:
            raise serializers.ValidationError({
                'valor': f'Valor excede o restante da venda. Restante: {restante:.2f}.'
            })

        if metodo == 'DINHEIRO':
            if valor_recebido is None:
                raise serializers.ValidationError({
                    'valor_recebido': 'Informe o valor recebido para pagamento em dinheiro.'
                })
            if valor_recebido < valor:
                raise serializers.ValidationError({
                    'valor_recebido': 'O valor recebido nao pode ser menor que o valor do pagamento.'
                })
        else:
            attrs['valor_recebido'] = None

        return attrs

    class Meta:
        model = Pagamento
        fields = '__all__'
        read_only_fields = ('user', 'troco')
