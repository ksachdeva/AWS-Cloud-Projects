from aws_cdk import RemovalPolicy, aws_dynamodb as dynamodb
from constructs import Construct


class DynamoDBConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        # create the dynamodb table
        self.recipes_table = dynamodb.Table(
            self,
            "chap4-recipes-table",
            table_name="recipes",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING,
            ),
            removal_policy=RemovalPolicy.DESTROY,
        )
