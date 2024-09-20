import requests
import re
import asyncio
import aiohttp
import aiofiles
import os
from pathlib import Path
from config import Config
from tqdm import tqdm
from loguru import logger
# URL of the file to be downloaded
base_url = "https://www2.census.gov/geo/tiger/TIGER2010BLKPOPHU/"



# Producer coroutine to generate URLs
async def producer(queue, base_url, matches):
    for match in matches:
        url = os.path.join(base_url, match)
        await queue.put(url)
        logger.info(f"Added {url} to the queue")

# Consumer coroutine to download files
async def consumer(queue,data_save_path):
    async with aiohttp.ClientSession() as session:
        while True:
            url = await queue.get()
            if url is None:
                break
            filename = url.split('/')[-1]
            save_path = data_save_path / filename
            if save_path.exists():
                print(f"File {filename} already exists")
                queue.task_done()
                continue
            
            # Get the file size
            async with session.head(url, headers=Config.HEADERS, cookies=Config.COOKIES, proxy=Config.PROXY) as response:
                if response.status != 200:
                    logger.error(f"Failed to get file size for {url} - status {response.status} - {response.reason}")
                    queue.task_done()
                    continue
                file_size = int(response.headers.get('Content-Length', 0))
            async with session.get(url,headers=Config.HEADERS,cookies=Config.COOKIES,proxy=Config.PROXY) as response:
                if response.status == 200:
                    logger.info(f"Downloading {filename} - {response.content_length} bytes")
                    with tqdm(total=response.content_length, unit='B', unit_scale=True, desc=filename) as pbar:
                        async with aiofiles.open(save_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(1024):
                                await f.write(chunk)
                                pbar.update(len(chunk))
                    logger.info(f"Downloaded {filename}")
                else:
                    logger.error(f"Failed to download {filename} - status {response.status} - {response.reason}")
            queue.task_done()
async def get_matches(base_url):
    async with aiohttp.ClientSession() as session:
         async with session.get(base_url,headers=Config.HEADERS,cookies=Config.COOKIES,proxy=Config.PROXY) as response:
            # Check if the request was successful
            matches = []
            if response.status == 200:
                # Save the content to a file
                html_content = await response.text('utf-8')
                # Regular expression to extract 'tabblock2010_02_pophu.zip'
                pattern = r'>(tabblock\d{4}_\d{2}_pophu\.zip)<'
                matches = re.findall(pattern, html_content)
                print("File downloaded successfully.")
            else:
                print(f"Failed to download file. Status code: {response.status}")
            return matches
# Main coroutine to set up producer and consumer tasks
async def main(base_url,data_save_path):
    if not data_save_path.exists():
        data_save_path.mkdir(parents=True)
    matches = await get_matches(base_url)
    queue = asyncio.Queue()
    producer_task = asyncio.create_task(producer(queue, base_url, matches))
    consumer_tasks = [asyncio.create_task(consumer(queue,data_save_path)) for _ in range(5)]

    await producer_task
    await queue.join()

    for _ in range(5):
        await queue.put(None)
    await asyncio.gather(*consumer_tasks)

if __name__ == '__main__':
    asyncio.run(main(base_url,Path('./data/census')))