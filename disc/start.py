from core.utils.constants import get_token, client


async def start_discord():
    token = get_token()
    await client.start(token)
