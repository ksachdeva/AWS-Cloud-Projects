from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import BundlingOptions
from constructs import Construct


class LambdaFunctionsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        recipes_table: dynamodb.Table,
    ) -> None:
        super().__init__(scope, construct_id)

        # create the lambda function
        # Note - basic role for lambda execution is automatically created by CDK
        self.auth_lambda = _lambda.Function(
            self,
            "chap4-auth-lambda",
            description="This is the auth lambda function",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="main.lambda_handler",
            code=_lambda.Code.from_asset("../code/backend/auth-test"),
        )

        self.get_recipes_lambda = _lambda.Function(
            self,
            "chap4-get-recipes-lambda",
            description="This is the get recipes lambda function",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="main.lambda_handler",
            code=_lambda.Code.from_asset("../code/backend/get-recipes"),
        )

        recipes_table.grant_read_data(self.get_recipes_lambda)

        # powertool_layer = _lambda.LayerVersion.from_layer_version_arn(
        #     self,
        #     "powertools-layer",
        #     "arn:aws:lambda:us-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV3-312-x86_64:4",
        # )

        self.create_recipe_lambda = _lambda.Function(
            self,
            "chap4-create-recipe-lambda",
            description="This is the create recipe lambda function",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="main.lambda_handler",
            code=_lambda.Code.from_asset(
                "../code/backend/post-recipe",
                bundling=BundlingOptions(
                    image=_lambda.Runtime(
                        "python3.12:latest-x86_64",
                        _lambda.RuntimeFamily.PYTHON,
                    ).bundling_image,
                    command=[
                        "bash",
                        "-c",
                        "pip install 'aws-lambda-powertools[all]' -t /asset-output && cp -au . /asset-output",
                    ],
                ),
            ),
            # layers=[powertool_layer],
        )

        recipes_table.grant_read_write_data(self.create_recipe_lambda)

        self.delete_recipe_lambda = _lambda.Function(
            self,
            "chap4-delete-recipe-lambda",
            description="This is the delete recipe lambda function",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="main.lambda_handler",
            code=_lambda.Code.from_asset("../code/backend/delete-recipe"),
        )

        recipes_table.grant_read_write_data(self.delete_recipe_lambda)

        self.like_recipe_lambda = _lambda.Function(
            self,
            "chap4-like-recipe-lambda",
            description="This is the like recipe lambda function",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="main.lambda_handler",
            code=_lambda.Code.from_asset("../code/backend/like-recipe"),
        )

        recipes_table.grant_read_write_data(self.like_recipe_lambda)
