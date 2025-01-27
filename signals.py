# tgshop/signals.py
from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from tgshop.models.productImage import ProductImage

@receiver(pre_save, sender=ProductImage)
def check_cover(sender, instance, **kwargs):
    if instance.is_cover:
        ProductImage.objects.filter(
            product=instance.product, 
            is_cover=True
        ).exclude(pk=instance.pk).update(is_cover=False)

@receiver(pre_delete, sender=ProductImage)
def delete_image_file(sender, instance, **kwargs):
    instance.image.delete(save=False)  # Удалить файл при удалении записи