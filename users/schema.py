from graphene.relay import Node
from graphene_django import DjangoObjectType
from django.contrib.auth import get_user_model
import graphene
import graphql_jwt
# from graphene_django.types import DjangoObjectType




# Define the UserType with the Node interface for global ID support
class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()
        interfaces = (Node,)
        fields = ( "id", "email", "first_name", "is_active", "last_name", "username", "date_joined", "is_staff", "is_superuser", "last_login", "stores" )
        # fields = ["id", "first_Name"]
        filter_fields = {
            'first_name': ['exact', 'icontains', 'istartswith'],       
        }

class MeType(DjangoObjectType):
    is_shop_owner =  graphene.Boolean()

    class Meta:
        model = get_user_model()
        interfaces = (Node,)
        fields = ["id", "email", "first_name", "is_active", "last_name", "username", "date_joined", "is_staff", "is_superuser", "last_login", 'stores' ]
        # exclude = ("model",)  # Exclude unintended fields

        filter_fields = {
            'first_name': ['exact', 'icontains', 'istartswith'],       
        }
    
    def resolve_is_shop_owner(self, info):
        user = info.context.user
        return user.groups.filter(name='shop_owners').exists()
        
    


# Example query for user


# Custom schema for authentication
class ObtainJSONWebToken(graphql_jwt.ObtainJSONWebToken):
    user = graphene.Field(UserType)

    @classmethod
    def resolve(cls, root, info, **kwargs):
        return cls(user=info.context.user)

class AuthMutations(graphene.ObjectType):
    token_auth = ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()

class MeQuery(graphene.ObjectType):
    me = graphene.Field(MeType)

    def resolve_me(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return None

        return user

# schema = graphene.Schema(query=Query, mutation=AuthMutations)



