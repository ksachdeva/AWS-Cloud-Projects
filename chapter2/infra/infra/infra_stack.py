from aws_cdk import (
    Stack,
    CfnOutput,
    RemovalPolicy,
    aws_s3 as s3,
    aws_cloudfront as cf,
    aws_s3_deployment as s3_deployment,
)
from constructs import Construct


class InfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # created the bucket
        bucket = s3.Bucket(
            self,
            "chap2-infra-bucket",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            auto_delete_objects=True,
            enforce_ssl=True,
        )

        # add the files from code to this bucket
        s3_deployment.BucketDeployment(
            self,
            "chap2-infra-bucket-deployment",
            sources=[s3_deployment.Source.asset("../code")],
            destination_bucket=bucket,
        )

        # create the cloudfront distribution
        oai = cf.OriginAccessIdentity(self, "chap2-infra-oai")
        oai.apply_removal_policy(RemovalPolicy.DESTROY)

        # grant above identity read access to the bucket
        bucket.grant_read(oai)

        cf_distribution = cf.CloudFrontWebDistribution(
            self,
            "chap2-infra-distribution",
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
