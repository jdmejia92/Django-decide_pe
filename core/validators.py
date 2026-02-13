import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class CustomPasswordValidator:
    def validate(self, password, user=None):
        rules = [
            (r'[A-Z]', 2, "2 letras mayúsculas"),
            (r'[a-z]', 2, "2 letras minúsculas"),
            (r'[0-9]', 2, "2 dígitos numéricos"),
            (r'[+\-*/]', 2, "2 signos (+, -, *, /)"),
            # Cuenta símbolos que NO sean alfanuméricos ni los signos anteriores
            (r'[^a-zA-Z0-9+\-*/]', 2, "2 símbolos adicionales"),
        ]

        errors = []
        
        if len(password) < 12:
            errors.append("Mínimo 12 caracteres")

        for regex, count, label in rules:
            if len(re.findall(regex, password)) < count:
                errors.append(f"Mínimo {label}")

        if errors:
            raise ValidationError(
                _("La contraseña no cumple los requisitos: " + ", ".join(errors)),
                code='password_too_weak',
            )

    def get_help_text(self):
        return _(
            "Min. 12 car., 2 mayús, 2 minús, 2 núm, 2 simb. y 2 signos (+-*/)."
        )