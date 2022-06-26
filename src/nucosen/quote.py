from datetime import timedelta
from logging import getLogger
from typing import Optional, Tuple, Dict, Any
from time import sleep

from requests import delete, get, post, patch
from requests.exceptions import ConnectionError, HTTPError
from retry import retry

from nucosen.sessionCookie import Session


class ReLoggedIn(Exception):
    pass


NetworkErrors = (HTTPError, ConnectionError, ReLoggedIn)


@retry(NetworkErrors, delay=1, backoff=2, logger=getLogger(__name__ + ".getCurrent"))
def getCurrent(liveId: str, session: Session) -> Optional[str]:
    url = "https://lapi.spi.nicovideo.jp/v1/tools/live/contents/{0}/quotation"
    resp = get(url.format(liveId), cookies=session.cookie)
    if resp.status_code == 403:
        session.login()
        raise ReLoggedIn("ログインセッション更新。連続してこのエラーが出た場合は異常です")
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    quotationData = dict(resp.json())
    quotationContent = quotationData.get("currentContent", {}).get("id", None)
    return quotationContent


@retry(NetworkErrors, delay=1, backoff=2, logger=getLogger(__name__ + ".stop"))
def stop(liveId: str, session: Session):
    url = "https://lapi.spi.nicovideo.jp/v1/tools/live/contents/{0}/quotation"
    resp = delete(url.format(liveId), cookies=session.cookie)
    if resp.status_code == 403:
        session.login()
        raise ReLoggedIn("ログインセッション更新。連続してこのエラーが出た場合は異常です")
    if resp.status_code == 404:
        getLogger(__name__).info("停止すべき引用が存在しませんでした。")
    resp.raise_for_status()


@retry(NetworkErrors, delay=1, backoff=2, logger=getLogger(__name__ + ".getViceoInfo"))
def getVideoInfo(videoId: str, session: Session) -> Tuple[bool, timedelta, str]:
    url = "https://lapi.spi.nicovideo.jp/v1/tools/live/quote/services/video/contents/{0}"
    resp = get(url.format(videoId), cookies=session.cookie)
    if resp.status_code == 403:
        session.login()
        raise ReLoggedIn("ログインセッション更新。連続してこのエラーが出た場合は異常です")
    if resp.status_code == 500:
        return (False, timedelta(seconds=0), "ERROR : このメッセージを見たら開発者へ連絡してください Twitter:@nucosen")
    resp.raise_for_status()
    videoData: Dict[str, Any] = dict(resp.json()).get("data", {})
    quotable = videoData.get("quotable", False)
    length = timedelta(seconds=videoData.get("length", 0))
    introducing = "{0} / {1}".format(
        videoData.get("title", "（無題）"),
        videoData.get("id", "sm0")
    )
    # NOTE - 戻り値: (引用可能性, 動画長, 紹介メッセージ)
    return (quotable, length, introducing)


@retry(NetworkErrors, delay=1, backoff=2, logger=getLogger(__name__ + ".once"))
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
    if resp.status_code == 403:
        session.login()
        raise ReLoggedIn("ログインセッション更新。連続してこのエラーが出た場合は異常です")
    resp.raise_for_status()
    postedVideoLength = getVideoInfo(videoId, session)[1]
    return postedVideoLength


def loop(liveId: str, videoId: str, session: Session):
    once(liveId, videoId, session)
    setLoop(liveId, session)


@retry(NetworkErrors, delay=1, backoff=2, logger=getLogger(__name__ + ".setLoop"))
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
        raise ReLoggedIn("ログインセッション更新。連続してこのエラーが出た場合は異常です")
    resp.raise_for_status()
