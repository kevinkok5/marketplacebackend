from store.models import StorePermission



STORE_PERMISSIONS = [
    "can_view",
    "can_edit_store",
    "can_edit_products",
    "can_create_products",
    "can_add_collaborators",
    "can_delete_products",
]


def assign_permission(store, user, **permissions):
    """
    Assign specific permissions to a user for a given store.
    :param store: Store object
    :param user: User object
    :param permissions: Permission key-value pairs (e.g., can_view=True, can_edit=True)
    :return: StorePermission object
    """
    # Fetch or create a StorePermission object for the user-store pair
    store_permission, created = StorePermission.objects.get_or_create(store=store, user=user)

    # Update permissions based on the provided keyword arguments
    for permission, value in permissions.items():
        if hasattr(store_permission, permission):
            setattr(store_permission, permission, value)

    # Save changes
    store_permission.save()
    return store_permission




def remove_permission(store, user, *permissions, delete_if_empty=True):
    """
    Remove specific permissions from a user for a given store.
    :param store: Store object
    :param user: User object
    :param permissions: List of permissions to remove (e.g., "can_view", "can_edit").
    :param delete_if_empty: If True, delete the permission record if all permissions are False.
    :return: StorePermission object or None if deleted.
    """
    try:
        store_permission = StorePermission.objects.get(store=store, user=user)

        # Remove specified permissions
        for permission in permissions:
            if hasattr(store_permission, permission):
                setattr(store_permission, permission, False)

        # Check if the record should be deleted
        if delete_if_empty and not any([
            store_permission.can_view,
            store_permission.can_edit_store,
            store_permission.can_edit_products,
            store_permission.can_add_collaborators,
            store_permission.can_delete_products,
            store_permission.can_create_products,
        ]):
            store_permission.delete()
            return None

        # Save changes
        store_permission.save()
        return store_permission

    except StorePermission.DoesNotExist:
        # If no permissions exist, there's nothing to remove
        return None





def set_permissions(store, user, delete_if_empty=True, **permissions, ):
    """
    Assign or remove specific permissions for a user on a store.
    :param store: Store object
    :param user: User object
    :param permissions: Permission key-value pairs (e.g., can_view=True, can_edit=False)
    :return: StorePermission object or None if deleted.
    """
    # Fetch or create the permission object
    store_permission, created = StorePermission.objects.get_or_create(store=store, user=user)

    # Update permissions
    for permission, value in permissions.items():
        if hasattr(store_permission, permission): # eg., hasattr(store_permission, "can_view")
            setattr(store_permission, permission, value) # eg., setattr(store_permission, "can_view", True)

    # Check if the record should be deleted (all permissions are False)
    # if delete_if_empty and not any([
    #     getattr(store_permission, "can_view"),
    #     getattr(store_permission, "can_edit_store"),
    #     getattr(store_permission, "can_edit_products"),
    #     getattr(store_permission, "can_create_products"),
    #     getattr(store_permission, "can_add_collaborators"),
    #     getattr(store_permission, "can_delete_products"),
    # ]):
    #     store_permission.delete()
    #     return None
    
    if delete_if_empty and not any(getattr(store_permission, attr) for attr in STORE_PERMISSIONS):
            store_permission.delete()
            return None

    # Save the updated permissions
    store_permission.save()
    return store_permission



def set_bulk_permissions(store, users_permissions):
    """
    Assign or remove permissions for multiple users on a store.
    :param store: Store object
    :param users_permissions: List of (user, permissions_dict) tuples
    :return: List of StorePermission objects
    """
    results = []
    for user, permissions in users_permissions:
        result = set_permissions(store, user, **permissions)
        results.append(result)
    return results




def user_has_store_permission(user, store, permission_type):
    """
    Check if a user has a specific permission on a store.
    :param user: User object
    :param store: Store object
    :permission_type (str): The permission type to check, from STORE_PERMISSIONS.
    :return: Boolean
    """

    if permission_type not in STORE_PERMISSIONS:
        raise ValueError(f"Invalid permission type: '{permission_type}'. Must be one of {STORE_PERMISSIONS}.")
    
    # If the user is the owner, grant all permissions
    if store.owner == user:
        return True

    # Check specific permission for the collaborator
    try:
        store_permission = StorePermission.objects.get(store=store, user=user)
        return getattr(store_permission, permission_type, False)
    except StorePermission.DoesNotExist:
        return False
    

def user_has_product_permission(user, product, permission_type):
    """
    Check if a user has a specific permission on a product.
    :param user: User object
    :param product: Product object
    :param permission_type: One of 'can_view', 'can_edit', 'can_delete', 'can_create'
    :return: Boolean
    """
    return user_has_store_permission(user, product.store, permission_type)



