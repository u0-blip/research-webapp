import graphene
import graphql_jwt


import user.schema as userSchema
import music.schema as MusicSchema

class Query(userSchema.Query, MusicSchema.Query):
    pass

class Mutation(userSchema.Mutation, MusicSchema.Mutation):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)