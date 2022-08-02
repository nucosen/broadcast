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

from datetime import datetime, time, timedelta, timezone
from logging import getLogger
from time import sleep
from typing import Any, Dict, List, Optional, Tuple
import sys

from requests import get, post, put
from requests.exceptions import ConnectionError as ConnError
from requests.exceptions import HTTPError
from requests.models import Response
from retry import retry

from nucosen.sessionCookie import Session


class NotExpectedResult(Exception):
    pass


class ReLoggedIn(Exception):
    pass


NetworkErrors = (HTTPError, ConnError, ReLoggedIn)
UserAgent = "NUCOSen Backend"


@retry(NetworkErrors, tries=5, delay=1, backoff=2, logger=getLogger(__name__ + ".getLives"))
def getLives(session: Session) -> Tuple[Optional[str], Optional[str]]:
    # NOTE - 戻り値 : (オンエア枠, 次枠)
    if session.cookie is None:
        session.login()
        raise ReLoggedIn("L00 ログインセッション更新")
    url = "https://live2.nicovideo.jp/unama/tool/v2/onairs/user"
    header = {
        "X-niconico-session": session.cookie.get("user_session"),
        "User-agent": UserAgent}
    resp = get(url, headers=header)
    if resp.status_code == 401:
        session.login()
        raise ReLoggedIn("L01 ログインセッション更新")
    resp.raise_for_status()
    result = dict(resp.json()).get("data", {})
    currentProgram = result.get("programId", None)
    nextProgram = result.get("nextProgramId", None)
    if nextProgram == currentProgram:
        nextProgram = None
    return (currentProgram, nextProgram)


def sGetLives(session: Session) -> Tuple[str, str]:
    result = getLives(session)
    if result[0] is None or result[1] is None:
        getLogger(__name__).critical("C0L 枠情報取得エラー {0} {1}".format(
            result[0], result[1]
        ))
        sys.exit(1)
    else:
        return (str(result[0]), str(result[1]))


@retry(NetworkErrors, tries=10, delay=1, backoff=2, logger=getLogger(__name__ + ".showMessage"))
def showMessage(liveId: str, msg: str, session: Session, *, permanent: bool = False):
    url = "https://live2.nicovideo.jp/watch/{0}/operator_comment".format(
        liveId)
    payload = {"text": msg, "isPermanent": permanent}
    header = {"User-Agent": UserAgent}
    resp = put(url, json=payload, headers=header, cookies=session.cookie)
    if resp.status_code in (403, 401):
        session.login()
        raise ReLoggedIn("L02 ログインセッション更新")
    resp.raise_for_status()


def generateLiveDict(category: str, communityId: str, tags: List[str]):
    tagDicts = []
    for tag in tags:
        tagDicts.append({"label": tag, "isLocked": True})
    return {
        "title": "【{0}】24時間引用配信【動画紹介】".format(category),
        "description": '<font size="+1">NUCOSenへようこそ！</font>' +
        '<br /><br />この生放送はBotにより自動的に配信されています。<br /><br />' +
        # '放送内容をリクエストしてみませんか？<br />連携サイト「NUCOSen LIVE」にて受け付けております！<br />' +
        # 'アクセスはこちらから → https://www.nucosen.live/<br />（リンク先で「{0}」を選択してください）'
        # .format(category),
        "",
        "category": "動画紹介",
        "tags": tagDicts,
        "communityId": communityId,
        "optionalCategories": [],
        "isTagOwnerLock": True,
        "isMemberOnly": False,
        "isTimeshiftEnabled": True,
        "isUadEnabled": True,
        "isAutoCommentFilterEnabled": False,
        "maxQuality": "1Mbps450p",
        "rightsItems": [],
        "isOfficialIchibaOnly": False,
        "isQuotable": False
    }


@retry(NetworkErrors, tries=10, delay=1, backoff=2, logger=getLogger(__name__ + ".takeReservation"))
def takeReservation(liveDict: Dict[Any, Any], startTime: datetime, duration: int, session: Session) -> Response:
    # TODO - This function SHOULD returns JSON decodable response ONLY.
    url = "https://live2.nicovideo.jp/unama/api/v2/programs"
    header = {
        "User-Agent": UserAgent,
        "X-niconico-session": session.getSessionString()
    }
    payload = liveDict
    payload["reservationBeginTime"] = startTime.strftime("%Y-%m-%dT%H:%M:%SZ")
    payload["durationMinutes"] = duration
    response = post(url=url, headers=header, json=payload)

    if response.status_code == 401:
        session.login()
        raise ReLoggedIn("L03 ログインセッション更新")
    if response.status_code == 400:
        # TODO メンテ以外の400リクエストを除外
        return response
    if response.status_code > 399:
        getLogger(__name__).info("枠予約失敗 : {0}".format(response.text))
        response.raise_for_status()

    return response


def getStartTimeOfNextLive(now: Optional[datetime] = None) -> datetime:
    JST = timezone(timedelta(hours=9))
    now = now or datetime.now(tz=JST)
    tomorrow = now.date() + timedelta(days=1)
    startCandidates = [
        datetime.combine(now.date(), time(hour=4, tzinfo=JST)),
        datetime.combine(now.date(), time(hour=10, tzinfo=JST)),
        datetime.combine(now.date(), time(hour=16, tzinfo=JST)),
        datetime.combine(now.date(), time(hour=22, tzinfo=JST)),
        datetime.combine(tomorrow, time(hour=4, tzinfo=JST))
    ]
    for startCondidate in startCandidates:
        if startCondidate >= now:
            break
    else:
        getLogger(__name__).error("E10 放送開始時刻算出エラー")
        startCondidate = datetime.combine(tomorrow, time(hour=10, tzinfo=JST))
    return startCondidate.astimezone(timezone.utc)


def reserveLiveToGetOverMaintenance(liveDict: Dict[Any, Any], defaultStartTime: datetime, session: Session):
    endTime = getStartTimeOfNextLive(defaultStartTime)
    currentDurationObject = endTime - defaultStartTime
    currentDuration = currentDurationObject.seconds // 60
    while currentDuration > 0:
        resp = takeReservation(
            liveDict, defaultStartTime, currentDuration, session)
        if resp.status_code == 201:
            break
        currentDuration -= 30
    else:
        getLogger(__name__).error("E20 枠予約失敗")

    currentStartTime: datetime = defaultStartTime + timedelta(currentDuration)
    for _ in range(10):
        endTime = getStartTimeOfNextLive(currentStartTime)
        liveDurationObject = endTime - currentStartTime
        liveDuration = liveDurationObject.seconds // 60
        resp = takeReservation(
            liveDict, currentStartTime, liveDuration, session)
        if resp.status_code == 201:
            break
        currentStartTime += timedelta(minutes=30)
    else:
        getLogger(__name__).error("E21 枠予約失敗")


@retry(NetworkErrors, tries=10, delay=1, backoff=2, logger=getLogger(__name__ + ".reserveLive"))
def reserveLive(category: str, communityId: str, tags: List[str], session: Session) -> None:
    liveDict = generateLiveDict(category, communityId, tags)
    startTime = getStartTimeOfNextLive()
    duration = 360

    response = takeReservation(liveDict, startTime, duration, session)
    responseJson: dict = response.json()
    responseMeta: dict = responseJson.get("meta", {})
    if not responseMeta.get("status", 0) in [201, 400]:
        getLogger(__name__).warning(
            "W20 枠予約失敗 {0}".format(responseJson))
        response.raise_for_status()
        return
    elif responseMeta["status"] == 201:
        getLogger(__name__).info("予約完了/{0}".format(responseJson))
    elif responseMeta.get("errorCode", "") == "OVERLAP_MAINTENANCE":
        reserveLiveToGetOverMaintenance(liveDict, startTime, session)
    else:
        response.raise_for_status()


@retry(NetworkErrors, tries=5, delay=1, backoff=2, logger=getLogger(__name__ + ".getStartTime"))
def getStartTime(liveId: str, session: Session) -> datetime:
    url = "https://live2.nicovideo.jp/unama/watch/{0}/programinfo"\
        .format(liveId)
    response = get(url, cookies=session.cookie)
    if response.status_code == 401:
        session.login()
        raise ReLoggedIn("L04 ログインセッション更新")
    response.raise_for_status()
    result = response.json()
    beginUnixTime = int(result["data"]["beginAt"])
    return datetime.fromtimestamp(beginUnixTime, timezone.utc)


def getEndTime(liveId: str, session: Session) -> datetime:
    url = "https://live2.nicovideo.jp/unama/watch/{0}/programinfo"\
        .format(liveId)
    response = get(url, cookies=session.cookie)
    if response.status_code == 401:
        session.login()
        raise ReLoggedIn("L05 ログインセッション更新")
    if response.status_code == 404:
        return datetime.now(timezone.utc)
    response.raise_for_status()
    result = response.json()
    beginUnixTime = int(result["data"]["endAt"])
    return datetime.fromtimestamp(beginUnixTime, timezone.utc)
