from django.contrib.auth.management.commands import createsuperuser
from django.core.exceptions import ValidationError
from users.models import User  # Assuming your user model is in 'users' app
from django.core import exceptions


class Command(createsuperuser.Command):
    def _custom_validate_username(self, username, verbose_field_name, database):
        # """Validate username. If invalid, return a string error message."""
        # if self.username_is_unique:
        try:
            if User.objects.filter(username=username).exists():
                raise ValidationError()
        except ValidationError as e:
            return "Error: That %s is already taken." % verbose_field_name
        else:
            pass

        try:
            self.username_field.clean(username, None)
        except exceptions.ValidationError as e:
            return "; ".join(e.messages)
     
            
    def handle(self, *args, **options):
        # Prompt for the username input separately
        username = options.get('username')
        if username:
                error_msg = self._custom_validate_username(
                    username, "username", User
                )
                if error_msg:
                    self.stderr.write(error_msg)
                    username = None

        while username is None:
            message = self._get_input_message(
                username, username
            )
            username = self.get_input_data(
                username, message, username
            )
            if username:
                error_msg = self._custom_validate_username(
                    username, "username", User
                )
                if error_msg:
                    self.stderr.write(error_msg)
                    username = None
                    continue
        return super().handle(*args, **options)
