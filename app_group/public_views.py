from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from app_group import invitations
from app_group.consent_markdown import render_consent_markdown
from app_group.models import CommonGroup


@sensitive_post_parameters()
@sensitive_variables()
@never_cache
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def member_consent(request, public_id, *, withdrawal=False):
    context = {"withdrawal": withdrawal}
    status = 200
    if request.method == "POST":
        secret = request.POST.get("secret", "")
        action = request.POST.get("action", "preview")
        try:
            if not secret or len(secret) > 128:
                raise ValidationError("Ce lien est invalide ou n'est plus disponible.")
            if withdrawal:
                if action not in {"preview", "delete"}:
                    raise ValidationError("Action invalide.")
                if action == "delete" and request.POST.get("confirmed") != "on":
                    raise ValidationError("La confirmation est obligatoire.")
                target = invitations.withdraw(
                    public_id, secret, confirm=action == "delete"
                )
                context.update(secret=secret, ready=True, done=action == "delete")
                if target is not None:
                    context.update(target)
                    context["group_name"] = CommonGroup.objects.get(
                        pk=target["group_id"]
                    ).name
            elif action == "preview":
                with transaction.atomic():
                    invitation = invitations.locked_invitation(public_id, secret)
                    context.update(
                        secret=secret,
                        ready=True,
                        first_name=invitation.first_name,
                        last_name=invitation.last_name,
                        group_name=CommonGroup.objects.get(pk=invitation.group_id).name,
                        consent_version=invitation.consent_version,
                        consent_html=render_consent_markdown(
                            invitation.consent_body_markdown
                        ),
                    )
            else:
                if action == "accept" and request.POST.get("confirmed") != "on":
                    raise ValidationError("La confirmation est obligatoire.")
                invitations.consent_decision(public_id, secret, action=action)
                context.update(done=True, accepted=action == "accept")
        except ValidationError as exc:
            context["error"] = " ".join(exc.messages)
            status = 400
    response = render(request, "app_group/public_consent.html", context, status=status)
    response["Referrer-Policy"] = "no-referrer"
    response["X-Robots-Tag"] = "noindex, nofollow, noarchive"
    response["Content-Security-Policy"] = (
        "default-src 'none'; style-src 'self'; script-src 'self'; connect-src 'self'; "
        "img-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"
    )
    return response
