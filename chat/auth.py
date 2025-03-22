import chainlit as cl
from dotenv import load_dotenv
from typing import Dict, Optional

# Load environment variables from .env file
load_dotenv()

# Auth0 authentication, allow all approved users
@cl.oauth_callback
def oauth_callback(
  provider_id: str,
  token: str,
  raw_user_data: Dict[str, str],
  default_user: cl.User,
) -> Optional[cl.User]:
  return default_user
