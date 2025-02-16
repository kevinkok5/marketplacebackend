
import graphene
from graphene.relay import Node
from graphql import GraphQLError
from .types import StoreType, ProductConnection, ProductUnion, ProductEdge, ProductMediasType, ItemCategoryType, VehicleCategoryType, HouseCategoryType
from store.models import Item_category, Vehicle_category, House_category, Product, Store, Media, Item, Vehicle, House
from graphene_django.filter import DjangoFilterConnectionField
# from api.views import APIException
from django.db import models
from store.permissions.permissions import user_has_store_permission, user_has_product_permission
# from api.functionTools import ResponsePayload





# ------------------------------------ Queries ---------------------------------
class CustomQuery(graphene.ObjectType):
    # Define the global success field
    success = graphene.Boolean()

    # Resolver for the success field
    def resolve_success(root, info):
        # By default, set success to True
        # Customize this logic based on the context or query
        return True


class StoreQueries(CustomQuery, graphene.ObjectType):
    all_stores = DjangoFilterConnectionField(StoreType)
    
    all_user_stores = DjangoFilterConnectionField(StoreType)

    all_item_categories = DjangoFilterConnectionField(ItemCategoryType)
    item_category = graphene.Field(ItemCategoryType, id=graphene.ID(required=True))  # global ID is passed
    all_vehicle_categories = DjangoFilterConnectionField(VehicleCategoryType)
    vehicle_category = graphene.Field(VehicleCategoryType, id=graphene.ID(required=True))  # global ID is passed
    all_house_categories = DjangoFilterConnectionField(HouseCategoryType)
    house_category = graphene.Field(HouseCategoryType, id=graphene.ID(required=True))  # global ID is passed

   
    all_products = graphene.Field(
        ProductConnection,
        first=graphene.Int(),
        after=graphene.String(),
        product_type=graphene.String(),  # Add this argument
        **{key: graphene.String() for key in ['name', 'make', 'model', 'condition', 'product_status']},
        **{key: graphene.Float() for key in ['price_min', 'price_max']}
    )

    store_products = graphene.Field(
        ProductConnection,
        first=graphene.Int(),
        after=graphene.String(),
        product_type=graphene.String(),  # Add this argument
        **{key: graphene.String() for key in ['name', 'make', 'model', 'condition', 'product_status']},
        **{key: graphene.Float() for key in ['price_min', 'price_max']}
    )


    product = graphene.Field(
        ProductUnion,
        id=graphene.ID(required=True),
    )
    user_product = graphene.Field(
        ProductUnion,
        id=graphene.ID(required=True),
    )
    all_medias = DjangoFilterConnectionField(ProductMediasType)
    # all_Houses = DjangoFilterConnectionField(HouseType)
    # all_Items = DjangoFilterConnectionField(ItemType)
    # all_Vehicles = DjangoFilterConnectionField(VehicleType)


    def resolve_all_stores(root, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("Authentication required.", extensions={"code": "UNAUTHENTICATED", "message": "Authentication required", "status": 401})
        if not user.is_superuser:
            raise GraphQLError("Authentication required.", extensions={"code": "FORBIDDEN", "message": "Not allowed", "status": 403})
        return Store.objects.all()
    
    def resolve_all_user_stores(root, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("Authentication required.", extensions={"code": "UNAUTHENTICATED", "message": "Authentication required", "status": 401})
        
        return Store.objects.filter(owner=user).all()
         
    
    def resolve_all_item_categories(root, info, **kwargs):
        user = info.context.user

        if not user.is_authenticated:
            raise GraphQLError("Authentication required.", extensions={"code": "UNAUTHENTICATED"})
        # if not user.is_superuser:
        #     raise GraphQLError("Not allowed.", extensions={"code": "FORBIDDEN"})
        return Item_category.objects.all()
    

    def resolve_item_category(root, info, id):

        return Node.get_node_from_global_id(info, id, only_type=Item_category)
    
    def resolve_all_vehicle_categories(root, info, **kwargs):
        return Vehicle_category.objects.all()
    def resolve_vehicle_category(root, info, id):
        return Node.get_node_from_global_id(info, id, only_type=Vehicle_category)
    
    def resolve_all_house_categories(root, info, **kwargs):
        return House_category.objects.all()
    def resolve_house_category(root, info, id):
        return Node.get_node_from_global_id(info, id, only_type=House_category)


    def resolve_all_products(self, info, first=None, after=None, product_type=None, **kwargs):
        user = info.context.user

        # Check if the user is authenticated
        if not user.is_authenticated:
            raise GraphQLError("Authentication required.", extensions={"code": "UNAUTHENTICATED"})


        # Extract filters from kwargs
        status = kwargs.get('product_status')
        price_min = kwargs.get('price_min')
        price_max = kwargs.get('price_max')
        name = kwargs.get('name')
        make = kwargs.get('make')
        model = kwargs.get('model')
        condition = kwargs.get('condition')

        # Start with a polymorphic query based on `type`
        if product_type == "Item":
            products = Product.productobjects.instance_of(Item)
            if name:
                products = products.filter(name__icontains=name)
            if condition:
                products = products.filter(condition=condition)

        elif product_type == "Vehicle":
            products = Product.productobjects.instance_of(Vehicle)
            if make:
                products = products.filter(make__icontains=make)
            if model:
                products = products.filter(model__icontains=model)
            if condition:
                products = products.filter(condition=condition)
        else:  # Query all products if no product_type is specified
            products = Product.productobjects.all()

        # # Apply permission-based filters
        # if user.is_superuser:  # Admins/Superusers can view all products
        #     pass
        # elif user.is_authenticated:  # Regular authenticated users
        # products = products.filter(
        #     # models.Q(owner=user) | 
        #     models.Q(product_status="published")
        # )

        # Apply common filters
        if status:
            products = products.filter(product_status=status)
        if price_min is not None:
            products = products.filter(price__gte=price_min)
        if price_max is not None:
            products = products.filter(price__lte=price_max)

        # Prefetch related data for efficiency
        products = products.prefetch_related('store', 'category')

        # Pagination logic
        start_index = 0
        if after:
            start_index = int(after)

        end_index = start_index + first if first else len(products)
        paginated_results = products[start_index:end_index]

        # Create edges for paginated results
        edges = [
            ProductEdge(node=item, cursor=str(index))
            for index, item in enumerate(paginated_results, start=start_index)
        ]

        # Construct PageInfo
        page_info = graphene.relay.PageInfo(
            has_next_page=end_index < products.count(),
            has_previous_page=start_index > 0,
            start_cursor=str(start_index) if edges else None,
            end_cursor=str(end_index - 1) if edges else None,
        )

        return ProductConnection(edges=edges, page_info=page_info)



    def resolve_store_products(self, info, first=None, after=None, product_type=None, **kwargs):
        user = info.context.user
        store = info.context.store

        # Check if the user is authenticated
        if not user.is_authenticated:
            return GraphQLError("Authentication required.")
        
        if store is None:
            return GraphQLError("No store associated with this request.")
        
        if not user_has_store_permission(user, store, "can_view"):
            return GraphQLError("You do not have permission to view this store's products.")


        # Extract filters from kwargs
        status = kwargs.get('product_status')
        price_min = kwargs.get('price_min')
        price_max = kwargs.get('price_max')
        name = kwargs.get('name')
        make = kwargs.get('make')
        model = kwargs.get('model')
        condition = kwargs.get('condition')

        # Start with products owned by the user
        products = Product.objects.filter(store=store)

        # Start with a polymorphic query based on `type`
        if product_type == "Item":
            products = products.instance_of(Item)
            if name:
                products = products.filter(name__icontains=name)
            if condition:
                products = products.filter(condition=condition)
        elif product_type == "Vehicle":
            products = products.instance_of(Vehicle)
            if make:
                products = products.filter(make__icontains=make)
            if model:
                products = products.filter(model__icontains=model)
            if condition:
                products = products.filter(condition=condition)

        # Apply common filters
        if status:
            products = products.filter(product_status=status)
        if price_min is not None:
            products = products.filter(price__gte=price_min)
        if price_max is not None:
            products = products.filter(price__lte=price_max)

        # Prefetch related data for efficiency
        products = products.prefetch_related('store', 'category')

        # Pagination logic
        start_index = 0
        if after:
            start_index = int(after)

        end_index = start_index + first if first else len(products)
        paginated_results = products[start_index:end_index]

        # Create edges for paginated results
        edges = [
            ProductEdge(node=item, cursor=str(index))
            for index, item in enumerate(paginated_results, start=start_index)
        ]

        # Construct PageInfo
        page_info = graphene.relay.PageInfo(
            has_next_page=end_index < products.count(),
            has_previous_page=start_index > 0,
            start_cursor=str(start_index) if edges else None,
            end_cursor=str(end_index - 1) if edges else None,
        )

        return ProductConnection(edges=edges, page_info=page_info)

    
    def resolve_product(self, info, id):
        user = info.context.user

        # Check if the user is authenticated
        if not user.is_authenticated:
            return GraphQLError("Authentication required.")
        
        


        # Decode the global ID
        try:
            type_name, db_id = Node.resolve_global_id(info, id)
            # print(f"type_name: {type_name} db_id: {db_id}")
        except Exception as e:
            raise ValueError(f"Invalid ID format: {e}")
        


        print("Resolved product...", db_id)



        # Resolve the instance based on the type name
        product = None
        if type_name == "ItemType":
            product = Item.productobjects.get(id=db_id)
        elif type_name == "VehicleType":
            product = Vehicle.productobjects.get(id=db_id)
        elif type_name == "HouseType":
            product = House.productobjects.get(id=db_id)
            
        else:
            raise ValueError("Invalid type for ProductUnion.")

        # Apply permission checks
        # if product.product_status == "published":
        #     return product  # Published products are viewable by anyone

        # if product.owner == user:
        #     return product  # Owners can view their own products regardless of status

        # Deny access if the user is neither the owner nor the product is published
        # raise GraphQLError("You do not have permission to view this product.")

        return product
    
    def resolve_user_product(self, info, id):
        user = info.context.user
        store = info.context.store


        # Check if the user is authenticated
        if not user.is_authenticated:
            return GraphQLError("Authentication required.")
        
        if store is None:
            return GraphQLError("No store associated with this request.")
        
        if not user_has_store_permission(user, store, "can_edit_products"):
            return GraphQLError("You do not have permission to view this store's products.")


        # Decode the global ID
        try:
            type_name, db_id = Node.resolve_global_id(info, id)
            # print(f"type_name: {type_name} db_id: {db_id}")
        except Exception as e:
            raise ValueError(f"Invalid ID format: {e}")
        


        print("Resolved product...", db_id)



        # Resolve the instance based on the type name
        product = None
        if type_name == "ItemType":
            product = Item.objects.get(id=db_id)
        elif type_name == "VehicleType":
            product = Vehicle.objects.get(id=db_id)
        elif type_name == "HouseType":
            product = House.objects.get(id=db_id)
            
        else:
            raise ValueError("Invalid type for ProductUnion.")

        # Apply permission checks
        # if product.product_status == "published":
        #     return product  # Published products are viewable by anyone

        # if product.owner == user:
        #     return product  # Owners can view their own products regardless of status

        # Deny access if the user is neither the owner nor the product is published
        # raise GraphQLError("You do not have permission to view this product.")

        return product