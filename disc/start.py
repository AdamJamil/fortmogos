from core.utils.constants import get_token, client
from disc.receive import on_error, on_message, on_reaction_add, on_ready


async def start_discord():
    client.event(on_ready)
    client.event(on_error)
    client.event(on_message)
    client.event(on_reaction_add)

    token = get_token()
    await client.start(token)
