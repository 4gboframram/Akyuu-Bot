"""
A quick and dirty wrapper around the mega api that trades a bit of security for 10x speed.
"""
import asyncio
import json
import random
import re
from copy import copy
from functools import wraps, partial
from io import BytesIO
from typing import NamedTuple, Optional, BinaryIO, Tuple

import aiohttp
from Crypto.Cipher import AES
from Crypto.Util import Counter
from aiofiles.base import AsyncBase
from aiofiles.threadpool import AsyncBufferedIOBase, wrap as _aiofiles_wrap
from mega import Mega
from mega.crypto import base64_to_a32, base64_url_decode, decrypt_attr, decrypt_key, a32_to_str, a32_to_base64, \
    base64_url_encode, encrypt_key
from tenacity import retry, wait_exponential, retry_if_exception_type

aiofiles_wrap = copy(_aiofiles_wrap)  # don't register it for all future aiofiles wrapping


@aiofiles_wrap.register(BytesIO)
def _(file, *, loop=None, executor=None):
    return AsyncBufferedIOBase(file, loop=loop, executor=executor)


async def file_wrap(file, *, loop=None, executor=None):
    if loop is None:
        loop = asyncio.get_event_loop()
    return aiofiles_wrap(file, loop=loop, executor=executor)


async def get_chunks(size):
    p = 0
    s = 0x20000
    while p + s < size:
        yield p, s
        p += s
        if s < 0x100000:
            s += 0x20000
    yield p, size - p


def unblock(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)

    return run


class UrlData(NamedTuple):
    shared_enc_key: str
    file_id: str
    root_folder: Optional[str]


class AsyncMega(Mega):
    NEW_STYLE_FOLDER_REGEX = re.compile(
        r"mega.[^/]+/folder/([0-z-_]+)#([0-z-_]+)(?:/folder/([0-z-_]+))*")
    OLD_STYLE_FOLDER_REGEX = re.compile(
        r"mega.[^/]+/#F!([0-z-_]+)[!#]([0-z-_]+)(?:/folder/([0-z-_]+))*")
    NEW_STYLE_FILE_IN_FOLDER_REGEX = re.compile(
        r'mega.[^/]+/folder/([0-z-_]+)#([0-z-_]+)/file/([0-z-_]+)')

    def __init__(self, options=None):
        super().__init__(options)
        self.async_session = aiohttp.ClientSession()

    @property
    def url(self) -> str:
        return f'{self.schema}://g.api.{self.domain}/cs'

    @retry(retry=retry_if_exception_type(RuntimeError),
           wait=wait_exponential(multiplier=2, min=2, max=60))
    async def async_api_request(self, data) -> dict:

        params = {'id': self.sequence_num}
        self.sequence_num += 1

        if self.sid:
            params.update({'sid': self.sid})

        # ensure input data is a list
        if not isinstance(data, list):
            data = [data]

        url = self.url

        async with self.async_session.post(url, params=params, json=data, timeout=self.timeout) as resp:
            json_resp = await resp.json()
        try:
            if isinstance(json_resp, list):
                int_resp = json_resp[0] if isinstance(json_resp[0],
                                                      int) else None
            elif isinstance(json_resp, int):
                int_resp = json_resp
        except IndexError:
            int_resp = None
        if int_resp is not None:
            if int_resp == 0:
                return int_resp
            if int_resp == -3:
                msg = 'Request failed, retrying'
                raise RuntimeError(msg)
            raise Exception(int_resp)
        return json_resp[0]

    async def close(self):
        await self.async_session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_t, exc_v, exc_tb):
        await self.close()
        return None

    @unblock
    def _login_process(self, resp, password_key):
        return super()._login_process(resp, password_key)

    @unblock
    def parse_url2(self, url: str) -> UrlData:
        if '/folder' in url:
            match = self.NEW_STYLE_FILE_IN_FOLDER_REGEX.search(url)
            if not match:
                raise ValueError(f"Invalid url {url}")

            return UrlData(match.group(2), match.group(3), match.group(1))
        else:
            return UrlData(*self._parse_url(url).split('!')[::-1], None)

    async def async_login_anonymous(self):
        master_key = [random.randint(0, 0xFFFFFFFF)] * 4
        password_key = [random.randint(0, 0xFFFFFFFF)] * 4
        session_self_challenge = [random.randint(0, 0xFFFFFFFF)] * 4

        user = await self.async_api_request({
            'a':
                'up',
            'k':
                a32_to_base64(encrypt_key(master_key, password_key)),
            'ts':
                base64_url_encode(
                    a32_to_str(session_self_challenge) +
                    a32_to_str(encrypt_key(session_self_challenge, master_key)))
        })

        resp = await self.async_api_request({'a': 'us', 'user': user})
        if isinstance(resp, int):
            raise Exception(resp)
        await self._login_process(resp, password_key)

    async def async_download_public_url(self, url: str, *, outfile: Optional[BinaryIO] = None) -> AsyncBase:
        """
        Asynchronously downloads a file to `outfile` if provided, otherwise creates a new in-memory file.
        This does not check the integrity of a file because that is really stupidly slow. It takes
        """
        url_data = await self.parse_url2(url)

        if url_data.root_folder:
            return await self._download_file_in_folder(url_data, out=outfile)
        else:
            file_key = base64_to_a32(url_data.shared_enc_key)

            file_data = await self.async_api_request({
                'a': 'g',
                'g': 1,
                'p': url_data.file_id
            })
            return await self._async_download_file(file_data, file_key, out=outfile)

    async def get_nodes_in_shared_folder(self, root_folder: str) -> dict:
        data = [{"a": "f", "c": 1, "ca": 1, "r": 1}]
        async with self.async_session.post(self.url, params={'id': self.sequence_num,
                                                             'n': root_folder},
                                           data=json.dumps(data)) as response:
            json_resp = await response.json()
        return json_resp[0]["f"]

    @staticmethod
    def decrypt_node_key(key_str: str, shared_key: str) -> Tuple[int, ...]:
        encrypted_key = base64_to_a32(key_str.split(":")[1])
        return decrypt_key(encrypted_key, shared_key)

    async def _download_file_in_folder(self, url_data: UrlData, out: Optional[BinaryIO] = None) -> AsyncBase:
        shared_key = base64_to_a32(url_data.shared_enc_key)
        nodes = await self.get_nodes_in_shared_folder(url_data.root_folder)
        file_key = None
        for node in nodes:
            key = self.decrypt_node_key(node['k'], shared_key)
            if node["t"] == 0:  # Is a file
                k = (
                    key[0] ^ key[4],
                    key[1] ^ key[5],
                    key[2] ^ key[6],
                    key[3] ^ key[7])
            elif node["t"] == 1:  # Is a folder
                k = key
            attrs = decrypt_attr(base64_url_decode(node["a"]), k)
            file_id = node["h"]
            if file_id == url_data.file_id:
                file_key = key
                break
        else:
            raise Exception(
                "File doesn't exist in folder??? This shouldn't happen???!!!")
        data = [{'a': 'g', 'g': 1, 'n': url_data.file_id}]

        async with self.async_session.post(
                self.url,
                params={'id': self.sequence_num,  # self.sequence_num
                        'n': url_data.root_folder},
                data=json.dumps(data)
        ) as resp:
            file_data = (await resp.json())[0]
        return await self._async_download_file(file_data, file_key, out)

    async def _async_download_file(self, file_data: dict, file_key: Tuple[int, ...],
                                   out: Optional[BinaryIO] = None) -> AsyncBase:

        k = (file_key[0] ^ file_key[4], file_key[1] ^ file_key[5],
             file_key[2] ^ file_key[6], file_key[3] ^ file_key[7])
        iv = file_key[4:6] + (0, 0)
        meta_mac = file_key[6:8]
        if 'g' not in file_data:
            raise Exception("File is not available anymore")
        file_url = file_data['g']
        file_size = file_data['s']

        out = out if out is not None else BytesIO()
        out = await file_wrap(out)

        # input_file = BytesIO()
        async with self.async_session.get(file_url) as resp:
            # that it doesn't work when just streaming the
            # content directly
            input_file = await file_wrap(BytesIO(await resp.content.read()))

            ##########
            # Decrypt
            ##########

            k_str = a32_to_str(k)
            counter = Counter.new(
                128, initial_value=(
                                           (iv[0] << 32) + iv[1]) << 64)
            aes = AES.new(k_str, AES.MODE_CTR, counter=counter)
            iv_str = a32_to_str([iv[0], iv[1], iv[0], iv[1]])

            async for chunk_start, chunk_size in get_chunks(file_size):
                chunk = await input_file.read(chunk_size)
                chunk = aes.decrypt(chunk)
                await out.write(chunk)

            return out
