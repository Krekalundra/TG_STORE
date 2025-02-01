from typing import Optional
from tgshop.models.customer import Customer

class CustomerService:
    @staticmethod
    def get_or_create_customer(telegram_id: int, **kwargs) -> Customer:
        """
        Получает существующего покупателя или создает нового по telegram_id
        
        Args:
            telegram_id: ID пользователя в Telegram
            **kwargs: поля для создания
            
        Returns:
            Customer: объект покупателя
        """
        customer, created = Customer.objects.get_or_create(
            telegram_id=telegram_id,
            defaults=kwargs
        )
        return customer, created

    @staticmethod
    def update_customer(customer: Customer, **kwargs) -> Customer:
        """
        Обновляет данные покупателя
        
        Args:
            customer: объект покупателя
            **kwargs: поля для обновления
            
        Returns:
            Customer: обновленный объект покупателя
        """
        for key, value in kwargs.items():
            setattr(customer, key, value)
        customer.save()
        return customer

    @staticmethod
    def get_customer(telegram_id: int) -> Optional[Customer]:
        """
        Получить покупателя по Telegram ID.
        
        Args:
            telegram_id (int): ID пользователя в Telegram
            
        Returns:
            Optional[Customer]: объект покупателя или None
        """
        try:
            return Customer.objects.get(telegram_id=telegram_id)
        except Customer.DoesNotExist:
            return None 