from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration
from aws_cdk.aws_apigatewayv2_authorizers import HttpJwtAuthorizer
from aws_cdk import CfnOutput
from constructs import Construct


class APIGatewayConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        user_pool_id: str,
        user_pool_client_id: str,
        auth_lambda: _lambda.Function,
        get_recipes_lambda: _lambda.Function,
        post_recipe_lambda: _lambda.Function,
        delete_recipe_lambda: _lambda.Function,
        like_recipe_lambda: _lambda.Function,
    ) -> None:
        super().__init__(scope, construct_id)

        # create the API Gateway
        api = apigwv2.HttpApi(
            self,
            "chap4-api-gateway",
            description="This is the API Gateway for the chap4 project",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_origins=["*"],
                allow_headers=["*"],
                allow_methods=[
                    apigwv2.CorsHttpMethod.GET,
                    apigwv2.CorsHttpMethod.POST,
                    apigwv2.CorsHttpMethod.OPTIONS,
                    apigwv2.CorsHttpMethod.DELETE,
                    apigwv2.CorsHttpMethod.PATCH,
                    apigwv2.CorsHttpMethod.PUT,
                ],
            ),
        )

        jwt_authorizer = HttpJwtAuthorizer(
            "jwtAuthorizer",
            f"https://cognito-idp.us-east-1.amazonaws.com/{user_pool_id}",
            jwt_audience=[user_pool_client_id],
        )

        api.add_routes(
            path="/auth",
            methods=[apigwv2.HttpMethod.GET],
            integration=HttpLambdaIntegration(
                "testAuthIntegration",
                handler=auth_lambda,
            ),
            authorizer=jwt_authorizer,
        )

        api.add_routes(
            path="/recipes",
            methods=[apigwv2.HttpMethod.GET],
            integration=HttpLambdaIntegration(
                "testGetRecipesIntegration",
                handler=get_recipes_lambda,
            ),
        )

        api.add_routes(
            path="/recipes",
            methods=[apigwv2.HttpMethod.POST],
            integration=HttpLambdaIntegration(
                "testCreateRecipeIntegration",
                handler=post_recipe_lambda,
            ),
            authorizer=jwt_authorizer,
        )

        api.add_routes(
            path="/recipes/{recipe_id}",
            methods=[apigwv2.HttpMethod.DELETE],
            integration=HttpLambdaIntegration(
                "testDeleteRecipeIntegration",
                handler=delete_recipe_lambda,
            ),
            authorizer=jwt_authorizer,
        )

        api.add_routes(
            path="/recipes/like/{recipe_id}",
            methods=[apigwv2.HttpMethod.PUT],
            integration=HttpLambdaIntegration(
                "testLikeRecipeIntegration",
                handler=like_recipe_lambda,
            ),
        )

        self.api = api

    def print_outputs(self):
        CfnOutput(
            self,
            "API Endpoint",
            value=self.api.api_endpoint,
            description="This is the endpoint of the API Gateway",
        )
