from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from store.models import Store  # Replace 'your_app' with your actual app name

class Command(BaseCommand):
    help = 'Create the shop_owners group and assign create and edit permissions for the Shop model.'

    def handle(self, *args, **kwargs):
        # Get or create the shop_owners group
        shop_owners_group, created = Group.objects.get_or_create(name='shop_owners')

        if created:

            # Get the content type for the Shop model
            shop_content_type = ContentType.objects.get_for_model(Store)

            # # Filter for add and change permissions
            # permissions = Permission.objects.filter(
            #     content_type=shop_content_type,
            #     codename__in=['add_shop', 'change_shop']
            # )

            # Get all CRUD permissions for the Shop model
            permissions = Permission.objects.filter(content_type=shop_content_type)

            # Assign the permissions to the group
            shop_owners_group.permissions.set(permissions)

            self.stdout.write(self.style.SUCCESS('Successfully created shop_owners group with permissions.'))
        else:
            self.stdout.write(self.style.SUCCESS('shop_owners group already exists.'))
