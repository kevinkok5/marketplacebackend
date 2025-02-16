
from functools import wraps
from django.http import HttpResponseForbidden
from store.models import Product
from .permissions import user_has_store_permission, STORE_PERMISSIONS
from django.shortcuts import get_object_or_404


from graphql import GraphQLError



def store_permission_required(permission_type: str):
    """
    Decorator to check if a user has a specific permission on a product.

    Args:
        permission_type (str): The permission type to check, from STORE_PERMISSIONS.

    Returns:
        function: The decorated function with permission checks.

    Raises:
        ValueError: If the permission_type is not valid.
    """
    if permission_type not in STORE_PERMISSIONS:
        raise ValueError(f"Invalid permission type: '{permission_type}'. Must be one of {STORE_PERMISSIONS}.")

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            try:
                # Determine context type: GraphQL or Django
                if len(args) > 0 and hasattr(args[0], 'context'):  # GraphQL
                    info = args[0]
                    user = info.context.user
                    product_id = kwargs.get("product_id")
                else:  # Django view
                    request = args[0]
                    user = request.user
                    product_id = kwargs.get("product_id")

                if not product_id:
                    raise ValueError("Product ID is required to check permissions.")

                # Fetch the product and check permissions
                product = get_object_or_404(Product, id=product_id)
                if product.owner != user and not user_has_store_permission(user, product, permission_type):
                    error_message = f"You do not have '{permission_type}' permission for this product."
                    if len(args) > 0 and hasattr(args[0], 'context'):  # GraphQL
                        raise GraphQLError(error_message)
                    return HttpResponseForbidden(error_message)

                return view_func(*args, **kwargs)

            except Exception as e:
                if len(args) > 0 and hasattr(args[0], 'context'):  # GraphQL
                    raise GraphQLError(str(e))
                return HttpResponseForbidden("An unexpected error occurred.")

        return wrapper
    return decorator


def group_shop_owner_permission_required(func):
    """
    Decorator to check if a user is part of the shop onwers group.
    :param permission_type: takes no arguments
    """
    @wraps(func)
    def wrapper(self, info, *args, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("You must be logged in to perform this action.")
        if not user.groups.filter(name='shop_owners').exists():
            raise GraphQLError("You do not have permission to create a store.")
        return func(self, info, *args, **kwargs)
    return wrapper

