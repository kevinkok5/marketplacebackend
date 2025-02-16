from django.shortcuts import get_object_or_404
from graphene.relay import Node
from graphene_django.filter import DjangoFilterConnectionField
from django.contrib.auth import get_user_model


# from graphene_file_upload.scalars import Upload
# from .serializers import ProductSerializer, MediaSerializer
# from .models import Product, Media
# from graphql import GraphQLError
# from .views import  APIException







import graphene
from users import schema as user_schema
from users import models as user_model
from store.schema import queries as store_queries, mutations as store_mutations




# from graphql_auth.schema import UserQuery, MeQuery
# from graphql_auth import mutations

# class AuthMutation(graphene.ObjectType):
#     register = mutations.Register.Field()
#     verify_account = mutations.VerifyAccount.Field()
#     resend_activation_email = mutations.ResendActivationEmail.Field()
#     send_password_reset_email = mutations.SendPasswordResetEmail.Field()
#     password_reset = mutations.PasswordReset.Field()
#     password_set = mutations.PasswordSet.Field() # For passwordless registration
#     password_change = mutations.PasswordChange.Field()
#     update_account = mutations.UpdateAccount.Field()
#     archive_account = mutations.ArchiveAccount.Field()
#     delete_account = mutations.DeleteAccount.Field()
#     send_secondary_email_activation =  mutations.SendSecondaryEmailActivation.Field()
#     verify_secondary_email = mutations.VerifySecondaryEmail.Field()
#     swap_emails = mutations.SwapEmails.Field()
#     remove_secondary_email = mutations.RemoveSecondaryEmail.Field()

#     # django-graphql-jwt inheritances
#     token_auth = mutations.ObtainJSONWebToken.Field()
#     verify_token = mutations.VerifyToken.Field()
#     refresh_token = mutations.RefreshToken.Field()
#     revoke_token = mutations.RevokeToken.Field()


class Query(user_schema.MeQuery, store_queries.StoreQueries, graphene.ObjectType):
    all_users = DjangoFilterConnectionField(user_schema.UserType)
    user = graphene.Field(user_schema.UserType, id=graphene.ID(required=True))  # global ID is passed

    

    # me = graphene.Field(user_schema.MeType)  # global ID is passed
   
    def resolve_all_users(root, info, **kwargs):
        return get_user_model().objects.all()


    def resolve_user(root, info, id):
        # return get_object_or_404(userModel.User, id=id)
        return Node.get_node_from_global_id(info, id, only_type=user_schema.UserType)
    


    
class Mutation(user_schema.AuthMutations, graphene.ObjectType):
    create_store = store_mutations.CreateStore.Field()
    become_shop_owner = store_mutations.BecomeShopOwner.Field()
    create_product = store_mutations.CreateProduct.Field()
    update_product = store_mutations.UpdateProduct.Field()
    delete_product = store_mutations.DeleteProduct.Field()


schema = graphene.Schema(query=Query, mutation=Mutation) 