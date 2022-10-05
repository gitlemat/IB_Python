import asyncio
import websockets
 
async def test():
    async with websockets.connect('ws://localhost:9999') as websocket:
        while True:
            name = input("> ")
    
            await websocket.send(name)
            greeting = ''
            while greeting != 'EOP':
                greeting = await websocket.recv()
                print(f"{greeting}")
 
asyncio.get_event_loop().run_until_complete(test())