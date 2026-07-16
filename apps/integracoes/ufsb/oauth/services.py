from .client import UFSBOAuthClient
from .schemas import OAuthToken, OAuthUserInfo


class AuthenticateUFSBUserService:
    def __init__(self, client: UFSBOAuthClient | None = None):
        self.client = client or UFSBOAuthClient()

    def execute(self, *, code: str, code_verifier: str | None = None) -> OAuthUserInfo:
        token: OAuthToken = self.client.exchange_code(
            code=code,
            code_verifier=code_verifier,
        )
        return self.client.fetch_user_info(token)
