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

from datetime import timedelta
from logging import getLogger
from typing import Optional, Tuple, Dict, Any
from time import sleep

from requests import delete, get, post, patch
from requests.exceptions import ConnectionError as ConnError
from requests.exceptions import HTTPError
from retry import retry

from nucosen.sessionCookie import Session

from xml.etree import ElementTree as ET


class ReLoggedIn(Exception):
    pass


NetworkErrors = (HTTPError, ConnError, ReLoggedIn)


@retry(NetworkErrors, tries=10, delay=1, backoff=2, logger=getLogger(__name__ + ".getCurrent"))
def getCurrent(liveId: str, session: Session) -> Optional[str]:
    url = "https://lapi.spi.nicovideo.jp/v1/tools/live/contents/{0}/quotation"
    resp = get(url.format(liveId), cookies=session.cookie)
    if resp.status_code == 403:
        session.login()
        raise ReLoggedIn("ログインセッション更新")
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    quotationData = dict(resp.json())
    quotationContent = quotationData.get("currentContent", {}).get("id", None)
    return quotationContent


@retry(NetworkErrors, tries=5, delay=1, backoff=2, logger=getLogger(__name__ + ".stop"))
def stop(liveId: str, session: Session):
    url = "https://lapi.spi.nicovideo.jp/v1/tools/live/contents/{0}/quotation"
    resp = delete(url.format(liveId), cookies=session.cookie)
    if resp.status_code == 403:
        session.login()
        raise ReLoggedIn("ログインセッション更新")
    if resp.status_code == 404:
        getLogger(__name__).info("停止すべき引用が存在しませんでした。")
    resp.raise_for_status()


@retry(NetworkErrors, tries=5, delay=1, backoff=2, logger=getLogger(__name__ + ".checkNgTag"))
def checkNgTag(videoId: str, ngTags: set) -> bool:
    url = "https://ext.nicovideo.jp/api/getthumbinfo/{0}"
    resp = get(url.format(videoId))
    resp.raise_for_status()
    videoThumbInfo = ET.fromstring(resp.text)
    tagsElement = videoThumbInfo.findall(".//tag")
    tags = set(map(lambda x: x.text, tagsElement))
    return True if len(ngTags | tags) == 0 else False


@retry(NetworkErrors, tries=3, delay=1, backoff=2, logger=getLogger(__name__ + ".getVideoInfo"))
def getVideoInfo(videoId: str, session: Session, ngTags: set) -> Tuple[bool, timedelta, str]:
    # NOTE - 戻り値: (引用可能性, 動画長, 紹介メッセージ)
    url = "https://lapi.spi.nicovideo.jp/v1/tools/live/quote/services/video/contents/{0}"
    resp = get(url.format(videoId), cookies=session.cookie)
    if resp.status_code == 403:
        session.login()
        raise ReLoggedIn("ログインセッション更新")
    if resp.status_code == 500:
        return (False, timedelta(seconds=0), "ERROR")
    resp.raise_for_status()
    videoData: Dict[str, Any] = dict(resp.json()).get("data", {})
    quotable = videoData.get("quotable", False)
    # NOTE : 重いので引用可能動画のみNGタグの処理を行う
    if quotable:
        quotable = checkNgTag(videoId, ngTags)
    length = timedelta(seconds=videoData.get("length", 0))
    introducing = "{0} / {1}".format(
        videoData.get("title", "（無題）"),
        videoData.get("id", "sm0")
    )
    return (quotable, length, introducing)


@retry(NetworkErrors, tries=10, delay=1, backoff=2, logger=getLogger(__name__ + ".once"))
def once(liveId: str, videoId: str, session: Session) -> timedelta:
    stop(liveId, session)

    # TODO - 音量をチェックする
    url = "https://lapi.spi.nicovideo.jp/v1/tools/live/contents/{0}/quotation"
    payload = {
        "layout": {
            "main": {
                "source": "quote",
                "volume": 0.5
            },
            "sub": {
                "source": "self",
                "volume": 0.5,
                "isSoundOnly": True
            }
        },
        "contents": [
            {
                "id": videoId,
                "type": "video"
            }
        ]
    }
    sleep(1.5)
    resp = post(url.format(liveId), json=payload, cookies=session.cookie)
    if resp.status_code == 409:
        resp = patch(
            (url + "/contents").format(liveId),
            json={"contents": [{"id": videoId, "type": "video"}]},
            cookies=session.cookie
        )
    if resp.status_code == 403:
        session.login()
        raise ReLoggedIn("ログインセッション更新")
    resp.raise_for_status()
    postedVideoLength = getVideoInfo(videoId, session, set())[1]
    return postedVideoLength


def loop(liveId: str, videoId: str, session: Session):
    once(liveId, videoId, session)
    setLoop(liveId, session)


@retry(NetworkErrors, tries=10, delay=1, backoff=2, logger=getLogger(__name__ + ".setLoop"))
def setLoop(liveId: str, session: Session):
    sleep(1)
    url = "https://lapi.spi.nicovideo.jp/v1/tools/live/contents/{0}/quotation/layout"
    payload = {
        "layout": {
            "main": {
                "source": "quote",
                "volume": 0.5
            },
            "sub": {
                "source": "self",
                "volume": 0.5,
                "isSoundOnly": False
            }
        },
        "repeat": True
    }
    resp = patch(url.format(liveId), json=payload, cookies=session.cookie)
    if resp.status_code == 403:
        session.login()
        raise ReLoggedIn("ログインセッション更新")
    resp.raise_for_status()
