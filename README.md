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

**Xavfsizlik:** `admin123` faqat development uchun. Productionda `DEBUG=False`, kuchli `SECRET_KEY`, HTTPS, `SESSION_COOKIE_SECURE=True`, haqiqiy `ALLOWED_HOSTS`, kuchli `DEFAULT_ADMIN_PASSWORD` va Telegram tokenini muhit o‘zgaruvchilarida o‘rnating. Sozlamalar productionda `admin123` bilan ishga tushishni rad etadi. Seed mavjud admin parolini faqat `python manage.py seed_data --reset-admin-password` berilganda yoki `RESET_ADMIN_PASSWORD_ON_SEED=True` qo‘yilganda yangilaydi.

## Railway deploy

Loyiha Railway uchun tayyor: `railway.json` build paytida `collectstatic`, deploy oldidan `migrate` va `seed_data`, startda esa `gunicorn`ni `$PORT`ga bind qiladi. `health/` endpoint Railway healthcheck uchun ishlatiladi. `Procfile` fallback sifatida bor, lekin asosiy sozlama `railway.json` orqali boshqariladi.

1. Railway’da yangi project yarating va GitHub repo orqali deploy qiling yoki lokal papkadan:

```powershell
railway up
```

2. Railway project canvas’da `PostgreSQL` service qo‘shing.
3. App service > Variables > Raw Editor bo‘limiga production qiymatlarini kiriting:

```env
DEBUG=False
SECRET_KEY=generate-a-long-random-secret
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=change-this-strong-password
RESET_ADMIN_PASSWORD_ON_SEED=False
SESSION_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
SECURE_REDIRECT_EXEMPT=^health/$
SECURE_HSTS_SECONDS=0
X_FRAME_OPTIONS=DENY
ALLOWED_HOSTS=${{RAILWAY_PUBLIC_DOMAIN}}
CSRF_TRUSTED_ORIGINS=https://${{RAILWAY_PUBLIC_DOMAIN}}
CREATE_DEMO_USERS=False
MEDIA_ROOT=/app/media

PGDATABASE=${{Postgres.PGDATABASE}}
PGUSER=${{Postgres.PGUSER}}
PGPASSWORD=${{Postgres.PGPASSWORD}}
PGHOST=${{Postgres.PGHOST}}
PGPORT=${{Postgres.PGPORT}}

TELEGRAM_BOT_TOKEN=
MINI_APP_URL=https://${{RAILWAY_PUBLIC_DOMAIN}}/
WEB_CONCURRENCY=2
```

`DATABASE_URL` yoki `DATABASE_PRIVATE_URL` berilsa, app ularni ham avtomatik ishlatadi.

4. Public URL uchun Railway service > Settings > Networking bo‘limidan domain generate qiling. Telegram Mini App ishlashi uchun `MINI_APP_URL` HTTPS Railway/custom domain bo‘lishi kerak.
5. Fayl uploadlari kerak bo‘lsa, Railway Volume qo‘shib mount path sifatida `/app/media` tanlang yoki `MEDIA_ROOT`ni volume mount pathga tenglang. Aks holda runtime fayllari deploylar orasida saqlanmasligi mumkin.

Healthcheck `service unavailable` bo‘lsa, app service deploy logs ichida healthcheckdan oldingi xatoni tekshiring. Eng ko‘p uchraydigan sabablar: `SECRET_KEY` yoki `DEFAULT_ADMIN_PASSWORD` production qiymati qo‘yilmagan, Postgres variables noto‘g‘ri reference qilingan, yoki service `$PORT`da tinglamayapti. Bu repo’da start command `sh railway/start.sh` orqali `$PORT`ni avtomatik ishlatadi.
