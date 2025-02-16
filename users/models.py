from django.db import models
from django.apps import apps
import uuid


from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

def generate_unique_username(email):
    base_username = email.split('@')[0]
    suffix = 1
    unique_username = base_username
    while get_user_model().objects.filter(username=unique_username).exists():
        unique_username = f"{base_username}{suffix}"
        suffix += 1
    return unique_username


# Create your models here.
class CustomUserManager(BaseUserManager):
    def _create_user(self, first_name, username, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not first_name:
            raise ValueError("The given first_name must be set")
       
        if not email:
            raise ValueError("The given email must be set")
        

        email = self.normalize_email(email)
        # Lookup the real model class from the global app registry so this
        # manager method can be used in migrations. This is fine because
        # managers are by definition working on the real model.
        print('username: ' + username)

        if not username:
            raise ValueError("The given username must be set")
        
        else: 
            if self.model.objects.filter(username=username).exists():
                raise ValidationError({'username': 'A user with that username already exists.'})


        # GlobalUserModel = apps.get_model(
        #     self.model._meta.app_label, self.model._meta.object_name
        # )
        # username = GlobalUserModel.normalize_username(username)
        user = self.model(first_name=first_name, username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, first_name, username=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(first_name, username, email, password, **extra_fields)

    def create_superuser(self, first_name, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(first_name, username, email, password, **extra_fields)

class User(AbstractUser):
    # username_validator = UnicodeUsernameValidator()


    first_name = models.CharField(_("first name"), max_length=150)
    email = models.EmailField(_('email address'), unique=True)
    # username = models.CharField(
    #     _("username"),
    #     max_length=150,
    #     unique=True,
    #     help_text=_(
    #         "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
    #     ),
    #     validators=[username_validator],
    #     error_messages={
    #         "unique": _("A user with that username already exists."),
    #     },
    # )

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "first_name"]

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = generate_unique_username(self.email)
        super().save(*args, **kwargs)

    
    # NOTE: I MIGHT NEED THIS (this is code in not functional yet check the constrains below)
    # def update(self, *args, **kwargs):
    #     if not self.username:
    #         # I'll check if the username is already set if not I'll
    #         # Generate username based on the email if not provided
    #         self.username = self.email.split('@')[0]
    #         suffix = 1
    #         while get_user_model().objects.filter(username=str(self.username)).exists():
    #             # If username exists, append a suffix to make it unique
    #             self.username = f"{self.username}{suffix}"
    #             suffix += 1
    #     super().save(*args, **kwargs)



    
# class TypeOfUser(models.Model):
#     TYPE_OPTIONS = [
#         ('shop_onwer', 'Shop_Owner'), 
#         ('blocked', 'Blocked'),
#     ]
#     user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
#     is_type = models.CharField(max_length=20, choices=TYPE_OPTIONS, default='owner')

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, primary_key=True)





    
