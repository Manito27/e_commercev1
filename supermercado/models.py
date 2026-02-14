from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from decimal import Decimal

# =========================
# PRODUTOS
# =========================

class CategoriaProduto(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class Produto(models.Model):
    nome = models.CharField(max_length=200)
    codigo_barras = models.CharField(max_length=50, unique=True, db_index=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    estoque = models.IntegerField(default=0)
    categoria = models.ForeignKey(CategoriaProduto, on_delete=models.PROTECT, related_name="produtos", blank=True, null=True)
    foto = models.ImageField(upload_to='produtos/', blank=True, null=True)
    descricao = models.CharField(max_length=1600, blank=True, null=True)

    def __str__(self):
        return f"{self.nome} ({self.codigo_barras})"


# =========================
# UTILIZADORES DO SISTEMA
# =========================

class Funcionario(models.Model):
    TIPO_DOC_CHOICES = [
        ('BI', 'Bilhete de Identidade'),
        ('PASSAPORTE', 'Passaporte'),
    ]
    user = models.OneToOneField(User,on_delete=models.CASCADE,unique=True,blank=True,null=True)
    nome = models.CharField(max_length=100)
    apelido = models.CharField(max_length=100)
    numero_documento = models.CharField(max_length=50,unique=True,blank=True,null=True)
    email = models.EmailField(blank=True, null=True)
    cargo = models.CharField(max_length=100,blank=True,null=True)

    def __str__(self):
        return f"{self.nome} {self.apelido}"
    
class Administrador(models.Model):
    TIPO_DOC_CHOICES = [
        ('BI', 'Bilhete de Identidade'),
        ('PASSAPORTE', 'Passaporte'),
    ]
    user = models.OneToOneField(User,on_delete=models.CASCADE,unique=True,blank=True,null=True)
    nome = models.CharField(max_length=100)
    apelido = models.CharField(max_length=100)
    numero_documento = models.CharField(max_length=50,unique=True,blank=True,null=True)
    email = models.EmailField(blank=True, null=True)
    cargo = models.CharField(max_length=100,blank=True,null=True)

    def __str__(self):
        return f"{self.nome} {self.apelido}"


# =========================
# CLIENTES
# =========================

class Cliente(models.Model):
    TIPO_DOC_CHOICES = [
        ('BI', 'Bilhete de Identidade'),
        ('PASSAPORTE', 'Passaporte'),
    ]

    nome = models.CharField(max_length=400)
    contacto = models.CharField(max_length=20,blank=True,null=True)
    tipo_documento = models.CharField(max_length=20,choices=TIPO_DOC_CHOICES,blank=True,null=True)
    numero_documento = models.CharField(max_length=50,unique=True,blank=True,null=True)
    morada = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome


# =========================
# VENDAS
# =========================

class Venda(models.Model):

    STATUS_CHOICES = [
        ('ABERTA', 'Aberta'),
        ('PAGA', 'Paga'),
        ('CANCELADA', 'Cancelada'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    data_venda = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ABERTA')

    def __str__(self):
        return f"Venda #{self.id}"

    def calcular_total(self):
        total = self.itens.aggregate(
            total=Sum('subtotal')
        )['total'] or Decimal('0.00')

        self.total = total
        self.save(update_fields=['total'])
        return total



class ItemVenda(models.Model):

    venda = models.ForeignKey(Venda, related_name='itens', on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)

    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):

        # herda preço automaticamente
        if not self.preco_unitario:
            self.preco_unitario = self.produto.preco

        # valida estoque
        if self.pk is None:
            if self.produto.estoque < self.quantidade:
                raise ValueError("Estoque insuficiente")

            self.produto.estoque -= self.quantidade
            self.produto.save()

        self.subtotal = self.quantidade * self.preco_unitario

        super().save(*args, **kwargs)

        # recalcula total da venda
        self.venda.calcular_total()

    def delete(self, *args, **kwargs):
        # devolve estoque ao remover item
        self.produto.estoque += self.quantidade
        self.produto.save()

        super().delete(*args, **kwargs)
        self.venda.calcular_total()

    def __str__(self):
        return f"{self.produto.nome} x {self.quantidade}"



# =========================
# PAGAMENTO
# =========================

class Pagamento(models.Model):

    METODOS = [
        ('DINHEIRO', 'Dinheiro'),
        ('CARTAO', 'Cartão'),
        ('TRANSFERENCIA', 'Transferência'),
        ('MBWAY', 'MBWay'),
    ]

    venda = models.ForeignKey(Venda, related_name='pagamentos', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    valor = models.DecimalField(max_digits=12, decimal_places=2)
    metodo = models.CharField(max_length=20, choices=METODOS)

    valor_recebido = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    troco = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    data_pagamento = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # calcula troco
        if self.metodo == 'DINHEIRO' and self.valor_recebido:
            self.troco = self.valor_recebido - self.valor
            super().save(update_fields=['troco'])

        # verifica se venda está paga
        total_pago = self.venda.pagamentos.aggregate(
            total=Sum('valor')
        )['total'] or Decimal('0.00')

        if total_pago >= self.venda.total:
            self.venda.status = 'PAGA'
            self.venda.save(update_fields=['status'])

    def __str__(self):
        return f"Pagamento Venda #{self.venda.id}"

