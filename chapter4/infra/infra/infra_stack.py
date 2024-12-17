from aws_cdk import Stack, CfnOutput
from constructs import Construct

from .backend.cognito import CognitoConstruct
from .backend.functions import LambdaFunctionsConstruct
from .backend.gateway import APIGatewayConstruct
from .backend.dynamodb import DynamoDBConstruct
from .frontend import FrontendConstruct


class InfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # create the Cognito user pool
        cognito = CognitoConstruct(self, "Cognito")

        # create the dynamodb table
        db = DynamoDBConstruct(self, "DynamoDB")

        lambda_fns = LambdaFunctionsConstruct(
            self,
            "LambdaFunctions",
            recipes_table=db.recipes_table,
        )

        api_gateway = APIGatewayConstruct(
            self,
            "APIGateway",
            user_pool_id=cognito.user_pool.user_pool_id,
            user_pool_client_id=cognito.user_pool_client.user_pool_client_id,
            auth_lambda=lambda_fns.auth_lambda,
            get_recipes_lambda=lambda_fns.get_recipes_lambda,
            post_recipe_lambda=lambda_fns.create_recipe_lambda,
            delete_recipe_lambda=lambda_fns.delete_recipe_lambda,
            like_recipe_lambda=lambda_fns.like_recipe_lambda,
        )

        # create the frontend
        front_end = FrontendConstruct(self, "Frontend")

        api_gateway.print_outputs()
        front_end.print_outputs()
        cognito.print_outputs()

        CfnOutput(
            self,
            "RegionOutput",
            value=self.region,
            description="The region this stack was deployed to",
        )
