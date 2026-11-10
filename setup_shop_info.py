import os
import django
from decouple import config

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    config('DJANGO_SETTINGS_MODULE', default='manglam_furniture.settings.dev'),
)
django.setup()

from shop_info.models import ShopInfo

shop_data = {
    'store_name': 'Manglam Furniture',
    'address': '10, Kalwar Rd, near Rawan Gate Road,\nOfficers Enclave, Jhotwara,\nJaipur, Rajasthan 302012',
    'map_embed_url': 'https://www.google.com/maps/search/?api=1&query=Manglam+Furniture%2C+Kalwar+Road%2C+Jhotwara%2C+Jaipur%2C+Rajasthan+302012',
    'phone_number': '9509606170',
    'whatsapp_number': '9782549345',
    'email': '',
    'opening_hours': 'Sunday – Saturday\n9:00 AM – 9:00 PM\nOpen Every Day',
    'about_text': 'Welcome to one of Jaipur\'s trusted destinations for quality furniture. From elegant sofas and comfortable beds to stylish dining sets, chairs, mattresses, and spacious almirahs, we have everything you need to make your home beautiful and comfortable.\n\nOur goal is simple: to help you create a home you truly love. We offer carefully selected furniture at great prices, along with friendly service and reliable after-sales support.\n\nWhether you are furnishing a new home or giving your space a fresh look, our team is here to help you find the perfect furniture for your style, comfort, and budget.'
}

shop_info = ShopInfo.objects.first()
if shop_info:
    for key, value in shop_data.items():
        setattr(shop_info, key, value)
    shop_info.save()
    print("ShopInfo updated successfully")
else:
    ShopInfo.objects.create(**shop_data)
    print("ShopInfo created successfully")
