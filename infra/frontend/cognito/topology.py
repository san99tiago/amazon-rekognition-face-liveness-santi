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

        self.cognito = cognito.UserPool(
            self, "RFL-Cognito-User-Pool", user_pool_name=rfl_stack.stack_name
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
