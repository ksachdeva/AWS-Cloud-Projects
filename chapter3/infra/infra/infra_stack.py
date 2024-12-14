""" Stack for Chapter 3 """

from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_cloudfront as cf,
    aws_s3_deployment as s3_deployment,
    CfnTag,
    CfnOutput,
    RemovalPolicy,
)
from constructs import Construct

_VPC_CIDR = "10.0.0.0/16"
_RECIPES_TABLE_NAME = "Recipes"

_USER_DATA = [
    "#!/bin/bash",
    "sudo apt update",
    "sudo apt install python-is-python3 nginx jq",
    """sudo cat << EOF > /etc/nginx/sites-available/fastapi
              server {
              listen 80;
              server_name ~.;
              location / {
              proxy_pass http://localhost:8000;
              }
              }EOF""",
    "sudo ln -s /etc/nginx/sites-available/fastapi /etc/nginx/sites-enabled/",
    "sudo systemctl restart nginx",
    # f"export RECIPE_TABLE_NAME={_RECIPES_TABLE_NAME}",
    # "git clone https://github.com/ksachdeva/fastapi-dynamodb-sample.git",
    # "cd fastapi-dynamodb-sample",
    # "curl -LsSf https://astral.sh/uv/install.sh | sh",
    # "/home/ubuntu/.local/bin/uv sync",
    # "/home/ubuntu/.local/bin/uv run fastapi run main.py",
]


class InfraStack(Stack):
    """Infra Stack"""

    def _create_vpc(self) -> tuple[ec2.Vpc, ec2.SecurityGroup, ec2.CfnKeyPair]:
        # create the VPC
        vpc = ec2.Vpc(
            self,
            "chap3-infra-vpc",
            max_azs=1,
            ip_addresses=ec2.IpAddresses.cidr(_VPC_CIDR),
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC,
                    name="Public",
                    cidr_mask=20,
                )
            ],
        )

        # Create Security Group
        sec_group = ec2.SecurityGroup(
            self,
            "chap3-MySecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,
        )

        sec_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(22),
            description="allow SSH access",
        )

        sec_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),
            description="allow HTTP access",
        )

        # Create Key Pair
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnKeyPair.html
        cfn_key_pair = ec2.CfnKeyPair(
            self,
            "chap3-MyCfnKeyPair",
            key_name="cdk-ec2-key-pair",
            tags=[CfnTag(key="key", value="value")],
        )

        return vpc, sec_group, cfn_key_pair

    def _create_dynamodb_table(self) -> dynamodb.Table:
        recipes_table = dynamodb.Table(
            self,
            "recipes",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING,
            ),
            removal_policy=RemovalPolicy.DESTROY,
        )

        return recipes_table

    def _create_ec2_instance(
        self,
        vpc: ec2.Vpc,
        sec_group: ec2.SecurityGroup,
        cfn_key_pair: ec2.CfnKeyPair,
        recipes_table: dynamodb.Table,
    ):

        user_data = "\n".join(_USER_DATA)

        # create a role
        role = iam.Role(
            self,
            "chap3-MyRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
        )

        # attach a policy that allows access to dynamodb receipes table
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:PutItem",
                    "dynamodb:GetItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Scan",
                ],
                resources=[recipes_table.table_arn],
            )
        )

        instance = ec2.Instance(
            self,
            "chap3-MyInstance",
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ec2.MachineImage.generic_linux(
                {
                    "us-east-1": "ami-00f3c44a2de45a590",
                }
            ),
            vpc=vpc,
            role=role,
            security_group=sec_group,
            associate_public_ip_address=True,
            key_name=cfn_key_pair.key_name,
            user_data=ec2.UserData.custom(user_data),
        )
        CfnOutput(self, "InstanceId", value=instance.instance_id)

    def _create_frontend(self):
        # created the bucket
        bucket = s3.Bucket(
            self,
            "chap3-frontend-bucket",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            auto_delete_objects=True,
            enforce_ssl=True,
        )

        # add the files from code to this bucket
        s3_deployment.BucketDeployment(
            self,
            "chap3-frontend-bucket-deployment",
            sources=[s3_deployment.Source.asset("../code/frontend/dist")],
            destination_bucket=bucket,
        )

        # create the cloudfront distribution
        oai = cf.OriginAccessIdentity(self, "chap3-frontend-oai")
        oai.apply_removal_policy(RemovalPolicy.DESTROY)

        # grant above identity read access to the bucket
        bucket.grant_read(oai)

        cf_distribution = cf.CloudFrontWebDistribution(
            self,
            "chap3-frontend-distribution",
            origin_configs=[
                cf.SourceConfiguration(
                    s3_origin_source=cf.S3OriginConfig(
                        s3_bucket_source=bucket,
                        origin_access_identity=oai,
                    ),
                    behaviors=[cf.Behavior(is_default_behavior=True)],
                )
            ],
        )

        # Output the bucket name
        CfnOutput(
            self,
            "BucketNameOutput",
            value=bucket.bucket_name,
            description="The name of the S3 bucket",
        )

        CfnOutput(
            self,
            "DistributionId",
            value=cf_distribution.distribution_id,
        )

        CfnOutput(
            self,
            "OAI",
            value=oai.origin_access_identity_id,
        )

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # create the VPC
        vpc, sec_group, cfn_key_pair = self._create_vpc()

        # create the DynamoDB table
        recepies_table = self._create_dynamodb_table()

        # create the EC2 instance
        self._create_ec2_instance(vpc, sec_group, cfn_key_pair, recepies_table)

        # create the frontend
        # self._create_frontend()
