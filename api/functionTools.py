import graphene
from graphene.types.generic import GenericScalar

class ResponsePayload(graphene.ObjectType):
    """
    format the data.
    :param success: Bool
    :param message : String
    :param status_code : int
    :data : GenericScalar (Generic data field for any type).
    :return:  dic
    """
    success = graphene.Boolean()
    message = graphene.String()
    status_code = graphene.Int()
    data = GenericScalar()  # Generic data field for any type