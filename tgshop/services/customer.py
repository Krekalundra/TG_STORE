from typing import Optional
from tgshop.models.customer import Customer

class CustomerService:
    @staticmethod
    def get_or_create_customer(telegram_id: int, first_name: Optional[str] = None, last_name: Optional[str] = None) -> tuple[Customer, bool]:
        """
        Получить или создать покупателя по Telegram ID.
        
        Args:
            telegram_id (int): ID пользователя в Telegram
            first_name (str, optional): Имя пользователя
            last_name (str, optional): Фамилия пользователя
            
        Returns:
            tuple[Customer, bool]: (объект покупателя, создан ли новый)
        """
        try:
            # Пытаемся найти существующего покупателя
            customer = Customer.objects.get(telegram_id=telegram_id)
            created = False
            
            # Обновляем имя и фамилию, если они изменились
            if (first_name and customer.first_name != first_name) or \
               (last_name and customer.last_name != last_name):
                customer.first_name = first_name
                customer.last_name = last_name
                customer.save()
                
        except Customer.DoesNotExist:
            # Создаем нового покупателя
            customer = Customer.objects.create(
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name
            )
            created = True
            
        return customer, created

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