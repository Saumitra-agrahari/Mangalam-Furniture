import random
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView

from catalog.models import Item
from core.cache import get_active_categories

User = get_user_model()


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_items"] = (
            Item.objects.filter(is_active=True, is_featured=True)
            .select_related("category")
            .prefetch_related("images")[:8]
        )
        context["categories"] = get_active_categories()[:6]
        return context


class ManglamAdminLoginView(LoginView):
    template_name = "admin/login.html"
    authentication_form = AuthenticationForm


def _get_reset_session(request):
    return request.session.get("admin_reset")


def _clear_reset_session(request):
    request.session.pop("admin_reset", None)


def _build_reset_state(email, pin=None):
    expires_at = (timezone.now() + timedelta(minutes=10)).isoformat()
    state = {"email": (email or "").strip().lower(), "expires_at": expires_at, "attempts": 0, "verified": False}
    if pin is not None:
        state["pin"] = str(pin)
    return state


@never_cache
def admin_forgot_password(request):
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip()
        if not email:
            messages.error(request, "Enter the admin email address to continue.")
            return render(request, "admin/forgot_password.html", {"email": email})

        active_admin = User.objects.filter(email__iexact=email, is_active=True, is_staff=True).first()
        if active_admin:
            pin = random.randint(100000, 999999)
            state = _build_reset_state(email, pin)
            request.session["admin_reset"] = state
            send_mail(
                subject="Manglam Furniture admin password reset code",
                message=(
                    f"Your Manglam Furniture admin reset code is {pin}. "
                    "This code is valid for 10 minutes."
                ),
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@localhost"),
                recipient_list=[active_admin.email],
                fail_silently=False,
            )
        else:
            request.session["admin_reset"] = _build_reset_state(email)

        messages.success(
            request,
            "If an active admin account exists for that email, a reset code has been sent.",
        )
        return redirect("admin_verify_pin")

    return render(request, "admin/forgot_password.html")


@never_cache
def admin_verify_pin(request):
    state = _get_reset_session(request)
    if not state:
        return redirect("admin_forgot_password")

    expires_at = state.get("expires_at")
    if expires_at and timezone.now() > datetime.fromisoformat(expires_at):
        _clear_reset_session(request)
        messages.error(request, "Your reset code has expired. Please request a new one.")
        return redirect("admin_forgot_password")

    if request.method == "POST":
        provided_pin = (request.POST.get("pin") or "").strip()
        stored_pin = state.get("pin")
        if not stored_pin:
            messages.error(request, "This reset code is no longer available.")
            return redirect("admin_forgot_password")

        if provided_pin != stored_pin:
            attempts = int(state.get("attempts", 0)) + 1
            state["attempts"] = attempts
            request.session["admin_reset"] = state
            if attempts >= 5:
                _clear_reset_session(request)
                messages.error(request, "Too many invalid attempts. Please request a new reset code.")
                return redirect("admin_forgot_password")
            messages.error(request, f"Invalid reset code. {5 - attempts} attempts remaining.")
            return render(request, "admin/verify_pin.html", {"email": state.get("email", "")})

        state["verified"] = True
        request.session["admin_reset"] = state
        return redirect("admin_reset_password")

    return render(request, "admin/verify_pin.html", {"email": state.get("email", "")})


@never_cache
def admin_reset_password(request):
    state = _get_reset_session(request)
    if not state or not state.get("verified"):
        return redirect("admin_forgot_password")

    email = state.get("email")
    if request.method == "POST":
        password = request.POST.get("new_password") or ""
        confirm_password = request.POST.get("confirm_password") or ""

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, "admin/reset_password.html", {"email": email})
        if password != confirm_password:
            messages.error(request, "Passwords do not match. Please try again.")
            return render(request, "admin/reset_password.html", {"email": email})

        user = User.objects.filter(email__iexact=email, is_active=True, is_staff=True).first()
        if not user:
            _clear_reset_session(request)
            messages.error(request, "Unable to update the admin password right now.")
            return redirect("admin_forgot_password")

        user.set_password(password)
        user.save(update_fields=["password"])
        _clear_reset_session(request)
        messages.success(request, "Your password has been reset successfully. You can now sign in.")
        return redirect("admin_login")

    return render(request, "admin/reset_password.html", {"email": email})


@never_cache
def admin_password_reset_done(request):
    return render(request, "admin/password_reset_done.html")
