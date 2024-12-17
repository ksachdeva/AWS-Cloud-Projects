from aws_cdk import (
    CfnOutput,
    RemovalPolicy,
    aws_s3 as s3,
    aws_cloudfront as cf,
    # aws_s3_deployment as s3_deployment,
)
from constructs import Construct


class FrontendConstruct(Construct):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        # created the bucket
        self.bucket = s3.Bucket(
            self,
            "chap4-fe-bucket",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            auto_delete_objects=True,
            enforce_ssl=True,
        )

        # add the files from code to this bucket
        # s3_deployment.BucketDeployment(
        #     self,
        #     "chap4-fe-bucket-deployment",
        #     sources=[s3_deployment.Source.asset("../code/frontend/dist")],
        #     destination_bucket=self.bucket,
        # )

        # create the cloudfront distribution
        oai = cf.OriginAccessIdentity(self, "chap4-fe-oai")
        oai.apply_removal_policy(RemovalPolicy.DESTROY)

        # grant above identity read access to the bucket
        self.bucket.grant_read(oai)

        self.cf_distribution = cf.CloudFrontWebDistribution(
            self,
            "chap4-fe-distribution",
            origin_configs=[
                cf.SourceConfiguration(
                    s3_origin_source=cf.S3OriginConfig(
                        s3_bucket_source=self.bucket,
                        origin_access_identity=oai,
                    ),
                    behaviors=[cf.Behavior(is_default_behavior=True)],
                )
            ],
        )

    def print_outputs(self):
        CfnOutput(
            self,
            "BucketNameOutput",
            value=self.bucket.bucket_name,
            description="The name of the S3 bucket",
        )

        CfnOutput(
            self,
            "DistributionId",
            value=self.cf_distribution.distribution_domain_name,
        )
