from constructs import Construct
from aws_cdk import aws_cognito as cognito, RemovalPolicy
from aws_cdk import custom_resources as aws_cr
from aws_cdk import CfnOutput

_ADMIN_EMAIL = "ksachdeva17@gmail.com"
_ADMIN_NAME = "Admin Sachdeva"
_ADMIN_PASSWORD = "Password123"


class CognitoConstruct(Construct):

    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        self.user_pool = cognito.UserPool(
            scope,
            "chap4-user-pool",
            user_pool_name="chap4-user-pool",
            password_policy=cognito.PasswordPolicy(
                min_length=6,
                require_digits=False,
                require_lowercase=False,
                require_uppercase=False,
                require_symbols=False,
            ),
            mfa=cognito.Mfa.OFF,
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True),
                family_name=cognito.StandardAttribute(
                    required=True, mutable=False
                ),  # noqa
                address=cognito.StandardAttribute(mutable=True, required=False),  # noqa
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            self_sign_up_enabled=True,
            removal_policy=RemovalPolicy.DESTROY,
        )

        self.user_pool_client = self.user_pool.add_client(
            "chap4-user-pool-client",
            auth_flows=cognito.AuthFlow(user_password=True, user_srp=True),
        )

        # add the domain name as well
        self.user_pool.add_domain(
            "chap4-user-pool-domain",
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix="chap4-up",
            ),
        )

        first_admin = aws_cr.AwsCustomResource(
            scope,
            "chap4-first-admin",
            on_create=aws_cr.AwsSdkCall(
                service="CognitoIdentityServiceProvider",
                action="adminCreateUser",
                parameters={
                    "UserPoolId": self.user_pool.user_pool_id,
                    "Username": _ADMIN_EMAIL,
                    "UserAttributes": [
                        {"Name": "email", "Value": _ADMIN_EMAIL},
                        {"Name": "name", "Value": _ADMIN_NAME},
                    ],
                },
                physical_resource_id=aws_cr.PhysicalResourceId.of(
                    f"first_admin_{_ADMIN_EMAIL}"
                ),
            ),
            on_delete=aws_cr.AwsSdkCall(
                service="CognitoIdentityServiceProvider",
                action="adminDeleteUser",
                parameters={
                    "UserPoolId": self.user_pool.user_pool_id,
                    "Username": _ADMIN_EMAIL,
                },
            ),
            policy=aws_cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=aws_cr.AwsCustomResourcePolicy.ANY_RESOURCE
            ),
        )

        force_admin_password = aws_cr.AwsCustomResource(
            scope,
            "chap4-force-admin-password",
            on_create=aws_cr.AwsSdkCall(
                service="CognitoIdentityServiceProvider",
                action="adminSetUserPassword",
                parameters={
                    "UserPoolId": self.user_pool.user_pool_id,
                    "Username": _ADMIN_EMAIL,
                    "Password": _ADMIN_PASSWORD,
                    "Permanent": True,
                },
                physical_resource_id=aws_cr.PhysicalResourceId.of(
                    "force_admin_password"
                ),
            ),
            policy=aws_cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=aws_cr.AwsCustomResourcePolicy.ANY_RESOURCE
            ),
        )

        force_admin_password.node.add_dependency(first_admin)

    def print_outputs(self):
        CfnOutput(
            self,
            "UserPoolIdOutput",
            value=self.user_pool.user_pool_id,
            description="The ID of the user pool",
        )

        CfnOutput(
            self,
            "UserPoolClientIdOutput",
            value=self.user_pool_client.user_pool_client_id,
            description="The ID of the user pool client",
        )
