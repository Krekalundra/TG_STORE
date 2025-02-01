from django.db import models
from tgshop.models.customer import Customer
from tgshop.models.product import Product
from asgiref.sync import sync_to_async

class Cart(models.Model):
    customer = models.OneToOneField(
        Customer,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name="Покупатель"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    class Meta:
        db_table = "tgshop_cart"
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"

    def __str__(self):
        return f"Корзина {self.customer}"

    def get_total_amount(self):
        return sum(item.get_cost() for item in self.items.all())

    async def get_total_amount_async(self):
        """Асинхронный метод получения общей суммы корзины"""
        items = await sync_to_async(list)(self.items.all())
        return sum(item.get_cost() for item in items)

class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Корзина"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name="Товар"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Количество"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата добавления"
    )

    class Meta:
        db_table = "tgshop_cartitem"
        verbose_name = "Позиция в корзине"
        verbose_name_plural = "Позиции в корзине"
        unique_together = ['cart', 'product']  # Один товар в корзине только один раз

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    def get_cost(self):
        return self.product.price * self.quantity 