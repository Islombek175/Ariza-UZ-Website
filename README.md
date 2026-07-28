# Ariza.uz

Django asosidagi, mobil-first fuqarolar murojaati tizimi. Telefon orqali autentifikatsiya, Telegram Mini App tekshiruvi, 6 bosqichli avtomatik saqlanuvchi murojaat, fayllar, server-side yo‘naltirish va bo‘limlar bo‘yicha ajratilgan boshqaruv panelini o‘z ichiga oladi.

## Ishga tushirish

```powershell
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

Telegram bot (HTTPS Mini App URL va token kerak):

```powershell
$env:TELEGRAM_BOT_TOKEN="..."
$env:MINI_APP_URL="https://example.uz/"
python bot.py
```

Testlar: `python manage.py test`

Development kirishlari:

- Super admin: `admin` / `admin123`
- Bo‘lim xodimi: `+998901111111` / `Operator123`
- Fuqaro: `+998901234567` / `Citizen123`

**Xavfsizlik:** `admin123` faqat development uchun. Productionda `DEBUG=False`, kuchli `SECRET_KEY`, HTTPS, `SESSION_COOKIE_SECURE=True`, haqiqiy `ALLOWED_HOSTS`, kuchli `DEFAULT_ADMIN_PASSWORD` va Telegram tokenini muhit o‘zgaruvchilarida o‘rnating. Sozlamalar productionda `admin123` bilan ishga tushishni rad etadi. Seed mavjud admin parolini faqat `python manage.py seed_data --reset-admin-password` berilganda yangilaydi.
