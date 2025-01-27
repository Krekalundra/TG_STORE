# Generated by Django 5.1.5 on 2025-01-27 05:58

import django.db.models.deletion
import imagekit.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
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
            },
        ),
        migrations.CreateModel(
            name='TelegramSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(blank=True, help_text='Получить у @BotFather', max_length=200, verbose_name='Telegram Token')),
                ('chat_id', models.CharField(blank=True, max_length=100, null=True, verbose_name='ID чата для уведомлений')),
            ],
            options={
                'verbose_name': 'Настройка Telegram',
                'verbose_name_plural': 'Настройки Telegram',
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Название')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='models.category', verbose_name='Родительская категория')),
            ],
            options={
                'verbose_name': 'Категория',
                'verbose_name_plural': 'Категории',
                'ordering': ['order'],
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
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='models.category', verbose_name='Категория')),
            ],
            options={
                'verbose_name': 'Товар',
                'verbose_name_plural': 'Товары',
            },
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', imagekit.models.fields.ProcessedImageField(upload_to='products/%Y/%m/%d/', verbose_name='Изображение')),
                ('is_cover', models.BooleanField(default=False, help_text='Главное изображение товара', verbose_name='Обложка')),
                ('order', models.PositiveIntegerField(default=0, help_text='Чем меньше число, тем выше в списке', verbose_name='Порядок')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='models.product', verbose_name='Товар')),
            ],
            options={
                'verbose_name': 'Фотография товара',
                'verbose_name_plural': 'Фотографии товаров',
                'ordering': ['order'],
            },
        ),
    ]
