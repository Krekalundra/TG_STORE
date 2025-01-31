from django.db import migrations, models
import django.db.models.deletion
import imagekit.models.fields
from imagekit.processors import ResizeToFill

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Название')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='tgshop.category', verbose_name='Родительская категория')),
            ],
            options={
                'verbose_name': 'Категория',
                'verbose_name_plural': 'Категории',
                'db_table': 'tgshop_category',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Operator',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(help_text='Без @ (например: johnsmith)', max_length=100, unique=True, verbose_name='Telegram username оператора')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
            ],
            options={
                'verbose_name': 'Оператор',
                'verbose_name_plural': 'Операторы',
                'db_table': 'tgshop_operator',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
                ('name', models.CharField(max_length=100, verbose_name='Название товара')),
                ('dis_product', models.TextField(blank=True, verbose_name='Описание')),
                ('price', models.DecimalField(decimal_places=2, max_digits=6, verbose_name='Цена')),
                ('price_type', models.CharField(choices=[('piece', 'За штуку'), ('gram', 'За грамм')], default='piece', max_length=10, verbose_name='Тип цены')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tgshop.category', verbose_name='Категория')),
            ],
            options={
                'verbose_name': 'Товар',
                'verbose_name_plural': 'Товары',
                'db_table': 'tgshop_product',
            },
        ),
        migrations.CreateModel(
            name='TelegramSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(blank=True, help_text='Получить у @BotFather', max_length=200, verbose_name='Telegram Token')),
                ('chat_id', models.CharField(blank=True, max_length=100, null=True, verbose_name='ID чата для уведомлений')),
                ('about', models.TextField(blank=True, max_length=500, null=True, verbose_name='О магазине')),
                ('ship_pay', models.TextField(blank=True, max_length=500, null=True, verbose_name='Доставка и оплата')),
                ('bonus', models.TextField(blank=True, max_length=500, null=True, verbose_name='Бонусная система')),
            ],
            options={
                'verbose_name': 'Настройка Telegram',
                'verbose_name_plural': 'Настройки Telegram',
                'db_table': 'tgshop_telegramsettings',
            },
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', imagekit.models.fields.ProcessedImageField(upload_to='products/%Y/%m/%d/', verbose_name='Изображение')),
                ('is_cover', models.BooleanField(default=False, help_text='Главное изображение товара', verbose_name='Обложка')),
                ('order', models.PositiveIntegerField(default=0, help_text='Чем меньше число, тем выше в списке', verbose_name='Порядок')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='tgshop.product', verbose_name='Товар')),
            ],
            options={
                'verbose_name': 'Фотография товара',
                'verbose_name_plural': 'Фотографии товаров',
                'ordering': ['order'],
                'db_table': 'tgshop_productimage',
            },
        ),
    ]