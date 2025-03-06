from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import telebot, dotenv
from .bots.student_group import bot

from .models import Lead

dotenv.load_dotenv(settings.BASE_DIR / '.env')

def home(request):
    return HttpResponse("Hello, World! Welcome to fillright.silvara.uz")


from django.shortcuts import render, redirect
from .models import Lead

def lead_form(request):
    if request.method == "POST":
        name = request.POST.get('name')
        phone_number = request.POST.get('phone_number')
        furniture_type = request.POST.get('furniture_type')

        if name and phone_number and furniture_type:  # Agar barcha maydonlar to‘ldirilgan bo‘lsa
            Lead.objects.create(name=name, phone_number=phone_number, furniture_type=furniture_type)
            request.session['form_submitted'] = True  # Sessiyada belgilab qo‘yamiz
            return redirect('success_page')  # Success sahifasiga yo‘naltiramiz

    return render(request, 'fillright/lead_form.html')


def success_page(request):
    if not request.session.get('form_submitted'):
        return redirect('lead_form')  # Foydalanuvchi formani yubormagan bo‘lsa, qaytarib yuboramiz

    # Form yuborilgandan keyin sessiya flagini olib tashlaymiz
    del request.session['form_submitted']
    return render(request, 'fillright/success.html')


# Admin sahifasiga kirish uchun statik kalit
STATIC_ROOM_KEY = "hello"

def custom_admin_login(request):
    if request.method == "POST":
        entered_key = request.POST.get("room_key")
        if entered_key == STATIC_ROOM_KEY:
            request.session["admin_authenticated"] = True
            return redirect("custom_admin_panel")  # Admin paneliga yo‘naltiramiz
        else:
            return HttpResponse("Noto‘g‘ri kalit! Qayta urinib ko‘ring.", status=403)

    return render(request, "fillright/admin_login.html")


def custom_admin_panel(request):
    if not request.session.get("admin_authenticated"):
        return redirect("custom_admin_login")

    leads = Lead.objects.all()  # Eng yangi lead'larni chiqaramiz
    return render(request, "fillright/admin_panel.html", {"leads": leads})

def admin_lead_detail(request, lead_id):
    if not request.session.get("admin_authenticated"):
        return redirect("custom_admin_login")

    lead = get_object_or_404(Lead, id=lead_id)
    return render(request, "fillright/admin_lead_detail.html", {"lead": lead})

def custom_admin_logout(request):
    request.session.pop("admin_authenticated", None)  # Admin sessiyasini o‘chiramiz
    return redirect("custom_admin_login")


@csrf_exempt
def webhook(request, token):
    if token != settings.TELEGRAM_BOT_TOKEN:
        return JsonResponse({"error": "Invalid token"}, status=403)

    if request.method == "POST":
        json_str = request.body.decode("UTF-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return JsonResponse({"status": "ok"})

    return JsonResponse({"error": "Invalid request"}, status=400)
