import colorama

inc = 0.2


async def whisper(transcript_queue):
    for i in range(40):
        chunk = f"Chunk {i}"
        print(
            colorama.Fore.BLUE + f"whisper: {i} sleeping 1 sec to simulate slow stream"
        )
        await asyncio.sleep(inc)
        transcript_queue.put_nowait((i, chunk))
    transcript_queue.put_nowait(None)
    return


async def request(str):
    for cr in str:
        await asyncio.sleep(inc / 2)
        yield cr
    return


async def batch_request(transcript_queue, response_queue, chunk_size=10):
    chunks = []
    while True:
        chunk = await transcript_queue.get()

        if chunk is None:
            break

        chunks.append(chunk)
        if len(chunks) > chunk_size:
            print(
                colorama.Fore.WHITE
                + f"Making request with {len(chunks)} chunks and simulating slow response"
            )
            await asyncio.sleep(1)
            async for request_chunk in request(chunks):
                response_queue.put_nowait(request_chunk)
            chunks = []

    # ensures the last chunk is sent
    async for request_chunk in request(chunks):
        response_queue.put_nowait(request_chunk)

    # ensures the response queue is closed
    response_queue.put_nowait(None)
    return


async def main():
    import asyncio

    transcript_queue = asyncio.Queue()
    response_queue = asyncio.Queue()

    asyncio.ensure_future(
        asyncio.gather(
            whisper(transcript_queue), batch_request(transcript_queue, response_queue)
        )
    )
    return response_queue


if __name__ == "__main__":
    import asyncio
    import colorama

    async def stream_from_queue():
        resp = await main()
        while resp:
            chunk = await resp.get()
            if chunk is None:
                break
            print(colorama.Fore.RED + "STREAMING_RESULTS:", chunk)

    asyncio.run(stream_from_queue())
