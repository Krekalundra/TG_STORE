from typing import Optional
from decimal import Decimal
from tgshop.models.cart import Cart, CartItem
from tgshop.models.customer import Customer
from tgshop.models.product import Product
import logging
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

class CartService:
    @staticmethod
    async def get_cart(customer: Customer) -> Optional[Cart]:
        """Получить корзину покупателя"""
        try:
            return await sync_to_async(Cart.objects.get)(customer=customer)
        except Cart.DoesNotExist:
            return None

    @staticmethod
    async def get_or_create_cart(customer: Customer) -> Cart:
        """Получить или создать корзину для покупателя"""
        cart, _ = await sync_to_async(Cart.objects.get_or_create)(customer=customer)
        return cart

    @staticmethod
    async def add_product(customer: Customer, product: Product, quantity: int) -> CartItem:
        """Добавить товар в корзину"""
        try:
            cart = await CartService.get_or_create_cart(customer)
            
            # Проверяем, есть ли уже такой товар в корзине
            cart_item, created = await sync_to_async(CartItem.objects.get_or_create)(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not created:
                # Если товар уже есть, увеличиваем количество
                cart_item.quantity += quantity
                await sync_to_async(cart_item.save)()
                
            logger.info(f"Товар {product.id} добавлен в корзину {cart.id} в количестве {quantity}")
            return cart_item
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении товара в корзину: {e}")
            raise 