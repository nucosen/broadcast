"""
Copyright 2022 NUCOSen運営会議

This file is part of NUCOSen Broadcast.

NUCOSen Broadcast is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

NUCOSen Broadcast is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with NUCOSen Broadcast.  If not, see <https://www.gnu.org/licenses/>.
"""

from logging import getLogger
from os import getcwd
from re import match
from typing import Dict, Iterable, List, Optional

from decouple import AutoConfig
from requests import delete, get, post
from requests.exceptions import ConnectionError as ConnError
from requests.exceptions import HTTPError
from retry import retry

NetworkErrors = (HTTPError, ConnError)


class RestDbIo(object):
    # TODO - 非同期実行ができるリクエストにスレッドを使って高速化
    def __init__(self):
        config = AutoConfig(getcwd())
        queueUrl = config("QUEUE_URL", default=None)
        requestUrl = config("REQUEST_URL", default=None)
        key = config("DB_KEY", default=None)
        if None in (queueUrl, requestUrl, key):
            getLogger(__name__).critical("環境変数を確認してください")
            raise Exception(
                "RestDbIoの環境変数が全て揃いませんでした。{0} {1} {2}".format(
                    queueUrl, requestUrl, key))
        header = {'x-apikey': str(key), 'cache-control': "no-cache"}

        self.isQueueUpdated: bool = True
        self.__queueUrl = str(queueUrl)
        self.__requestUrl = str(requestUrl)
        self.__header = header
        self.__dequeueCache: List[Dict[str, str]] = []

    @retry(NetworkErrors, delay=1, backoff=2, logger=getLogger(__name__ + ".dequeue"))
    def dequeue(self) -> str | None:
        if self.isQueueUpdated:
            # 優先・エンキュー逆順
            query = '?q={}&h={"$orderby": {"priority": 1,"_id":-1}}'
            resp = get(self.__queueUrl + query, headers=self.__header)
            resp.raise_for_status()
            queues: List[Dict[str, str]] = resp.json()
            self.__dequeueCache = queues
            self.isQueueUpdated = False

        if len(self.__dequeueCache) < 1:
            return None
        result = self.__dequeueCache.pop()
        self.__deleteQueueItem(result["_id"])
        return result["videoId"]

    @retry(NetworkErrors, delay=1, backoff=2, logger=getLogger(__name__ + ".__deleteQueueItem"))
    def __deleteQueueItem(self, itemId: str):
        resp = delete(self.__queueUrl+"/"+itemId, headers=self.__header)
        resp.raise_for_status()

    @retry(NetworkErrors, delay=1, backoff=2, logger=getLogger(__name__ + ".enqueueByList"))
    def enqueueByList(self, items: Iterable[str]):
        payload = list()
        for item in items:
            if match("^[a-z][a-z][0-9]+$", item):
                payload.append({"videoId": item})
            else:
                getLogger(__name__).error(
                    "アボート:無効な動画IDでの通常エンキュー。{0}".format(item))
        if len(payload) < 1:
            return
        resp = post(self.__queueUrl, json=payload, headers=self.__header)
        resp.raise_for_status()
        self.isQueueUpdated = True

    @retry(NetworkErrors, delay=1, backoff=2, logger=getLogger(__name__ + ".priorityEnqueue"))
    def priorityEnqueue(self, item: str):
        if not match("^[a-z][a-z][0-9]+$", item):
            getLogger(__name__).error("アボート:無効な動画IDでの優先エンキュー。{0}".format(item))
            return
        payload = {"videoId": item, "priority": True}
        resp = post(self.__queueUrl, json=payload, headers=self.__header)
        resp.raise_for_status()
        self.isQueueUpdated = True

    @retry(NetworkErrors, delay=1, backoff=2, logger=getLogger(__name__ + ".getAndResetRequests"))
    def getAndResetRequests(self) -> Optional[List[str]]:
        resp = get(self.__requestUrl, headers=self.__header)
        resp.raise_for_status()
        results: List[Dict[str, str]] = resp.json()
        if len(results) < 1:
            return None
        deletionIds = []
        requestVideoIds = []
        for result in results:
            deletionIds.append(result["_id"])
            requestVideoIds.append(result["videoId"])
        self.__deleteRequestItems(deletionIds)
        return requestVideoIds

    @retry(NetworkErrors, delay=1, backoff=2, logger=getLogger(__name__ + ".__deleteRequestItems"))
    def __deleteRequestItems(self, items: List[str]):
        resp = delete(
            self.__requestUrl+"/*", json=items, headers=self.__header)
        resp.raise_for_status()
