from django.contrib import admin
from .models import (
    CategoriaProduto, Produto,
    Funcionario, Cliente, Venda, ItemVenda, Pagamento,Administrador
)


class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    extra = 0
# =========================
# PRODUTOS
# =========================




@admin.register(CategoriaProduto)
class CategoriaProdutoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome',)
    search_fields = ('nome',)


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'nome', 'codigo_barras',
        'categoria', 'preco', 'estoque','foto','descricao'
    )
    list_filter = ('categoria',)
    search_fields = ('nome', 'codigo_barras')
    ordering = ('nome',)

# =========================
# FUNCIONÁRIO
# =========================

@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'apelido', 'cargo')
    search_fields = ('nome', 'apelido', 'cargo')
    list_filter = ('cargo',)


# =========================
# Admin
# =========================

@admin.register(Administrador)
class AdministradorAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'apelido', 'cargo')
    search_fields = ('nome', 'apelido', 'cargo')
    list_filter = ('cargo',)


# =========================
# CLIENTE
# =========================

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome',  'contacto','morada',)
    search_fields = ('nome', 'contacto')
    ordering = ('nome',)


# =========================
# FATURA
# =========================
@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'user', 'total', 'status', 'data_venda')
    list_filter = ('status', 'data_venda')
    inlines = [ItemVendaInline]

# =========================
# ITEM VENDA
# =========================

@admin.register(ItemVenda)
class ItemVendaAdmin(admin.ModelAdmin):
    list_display = ['produto', 'venda', 'quantidade', 'preco_unitario', 'subtotal']
    search_fields = ['produto__nome', 'venda__id']


# =========================
# PAGAMENTO
# =========================

@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ('id', 'venda', 'valor', 'metodo', 'user', 'data_pagamento')
    list_filter = ('metodo', 'data_pagamento')
