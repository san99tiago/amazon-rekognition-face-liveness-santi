import builtins
from infra.interfaces import IRflStack
from constructs import Construct
from os import path
from aws_cdk import aws_iam as iam, aws_cognito as cognito

root_directory = path.dirname(__file__)
bin_directory = path.join(root_directory, "bin")


class FaceLivenessCognito(Construct):
    """
    Represents the root construct to create Amplify APP
    """

    def __init__(
        self, scope: Construct, id: builtins.str, rfl_stack: IRflStack
    ) -> None:
        super().__init__(scope, id)

        # Create Cognito User Pool
        self.cognito = cognito.UserPool(
            self,
            "RFL-Cognito-UserPool",
            user_pool_name=rfl_stack.stack_name,
            self_sign_up_enabled=True,  # Allow self-signup
            auto_verify=cognito.AutoVerifiedAttrs(
                email=True,  # Automatically verify emails
            ),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(
                    required=True, mutable=True
                ),  # Email is required
                phone_number=cognito.StandardAttribute(
                    required=True, mutable=True
                ),  # Optional phone number
            ),
            user_verification=cognito.UserVerificationConfig(
                email_subject="Verify Your Email for RUFUS BANK!",
                email_body="Hello, thank you for signing up. Please verify your email by clicking on the link: {####}",
                sms_message="Hello, use this code to verify your phone number: {####}",
            ),
        )

        self.client = cognito.UserPoolClient(
            self,
            "RFL-Cognito-Client",
            user_pool=self.cognito,
            user_pool_client_name=rfl_stack.stack_name,
        )

        self.idp = cognito.CfnIdentityPool(
            self,
            "RFL-IdentityPool",
            identity_pool_name=rfl_stack.stack_name,
            allow_unauthenticated_identities=True,
            cognito_identity_providers=[
                cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
                    client_id=self.client.user_pool_client_id,
                    provider_name=self.cognito.user_pool_provider_name,
                    server_side_token_check=None,
                )
            ],
        )

        # Create an IAM role with access to the specific DynamoDB table
        self.authrole = iam.Role(
            self,
            "RFLIdentityPoolAuthRole",
            assumed_by=iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                conditions={
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": self.idp.ref
                    },
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
            description="Role for authenticated users of the RFL app",
            role_name=f"{rfl_stack.stack_name}-AuthRole",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonRekognitionFullAccess"
                )
            ],
        )

        # Attach a custom policy to allow access to the specific DynamoDB table
        self.authrole.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Query",
                    "dynamodb:Scan",
                ],
                resources=["arn:aws:dynamodb:*:*:table/rufus-bank-auth-sessions-prod"],
            )
        )

        self.idpAttachment = cognito.CfnIdentityPoolRoleAttachment(
            self,
            "RFL-IdentityPool-Role-Attachment",
            identity_pool_id=self.idp.ref,
            roles={"authenticated": self.authrole.role_arn},
        )
