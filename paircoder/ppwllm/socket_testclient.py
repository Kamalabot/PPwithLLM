from websockets import connect
import json
import asyncio


async def chat_client():
    async with connect('ws://127.0.0.1:8000/ws/chat/lobby/') as chany:
        while True:
            nid = input("chat me: ")
            await chany.send(json.dumps({"message": nid}))
            recd_msg = await chany.recv()
            print(recd_msg)


if __name__ == '__main__':
    asyncio.run(chat_client())
    # sync_chat_client()