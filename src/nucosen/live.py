from datetime import datetime, time, timedelta, timezone
from logging import getLogger
from time import sleep
from typing import Any, Dict, List, Optional, Tuple

from requests import get, post, put
from requests.exceptions import ConnectionError, HTTPError
from requests.models import Response
from retry import retry

from nucosen.sessionCookie import Session


class ReLoggedIn(Exception):
    pass


class NotExpectedResult(Exception):
    pass


NetworkErrors = (HTTPError, ConnectionError, ReLoggedIn)
UserAgent = "NUCOSen Backend"


@retry(NetworkErrors, delay=1, backoff=2, logger=getLogger(__name__))
def getLives(session: Session) -> Tuple[Optional[str], Optional[str]]:
    # NOTE - 戻り値 : (オンエア枠, 次枠)
    if session.cookie is None:
        session.login()
        raise ReLoggedIn("ログインセッション更新。発生箇所:GL1")
    url = "https://live2.nicovideo.jp/unama/tool/v2/onairs/user"
    header = {
        "X-niconico-session": session.cookie.get("user_session"),
        "User-agent": UserAgent}
    resp = get(url, headers=header)
    if resp.status_code == 401:
        session.login()
        raise ReLoggedIn("ログインセッション更新。発生箇所:GL2")
    resp.raise_for_status()
    result = dict(resp.json()).get("data", {})
    currentProgram = result.get("programId", None)
    nextProgram = result.get("nextProgramId", None)
    return (currentProgram, nextProgram)


@retry(NotExpectedResult, delay=1, backoff=2, logger=getLogger(__name__))
def sGetLives(session: Session) -> Tuple[str, str]:
    result = getLives(session)
    if result[0] is None or result[1] is None:
        raise NotExpectedResult(
            "取得した枠情報が期待される値ではありませんでした。{0} {1}".format(result[0], result[1]))
    else:
        return (str(result[0]), str(result[1]))


@retry(NetworkErrors, delay=1, backoff=2, logger=getLogger(__name__))
def showMessage(liveId: str, msg: str, session: Session, *, permanent: bool = False):
    url = "https://live2.nicovideo.jp/watch/{0}/operator_comment".format(liveId)
    payload = {"text": msg, "isPermanent": permanent}
    header = {"User-Agent": UserAgent}
    resp = put(url, json=payload, headers=header, cookies=session.cookie)
    if resp.status_code in (403, 401):
        session.login()
        raise ReLoggedIn("ログインセッション更新。発生箇所:SM2")
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
        ""
        .format(category),
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


@retry(NetworkErrors, delay=1, backoff=2, logger=getLogger(__name__))
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
        raise ReLoggedIn("ログインセッション更新。発生箇所:TR")
    if response.status_code > 399:
        getLogger(__name__).error("枠予約失敗 : {0}".format(response.text))
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
        if startCondidate < now:
            continue
        return startCondidate.astimezone(timezone.utc)
    else:
        getLogger(__name__).error("次枠の適切な開始時刻が見つかりませんでした")
        sleep(0.1)
        return getStartTimeOfNextLive()


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
        getLogger(__name__).warning("メンテ前の枠が取得できなかったかもしれません。")

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
        getLogger(__name__).warning("メンテ後の枠が取得できなかったかもしれません。")


@retry(NetworkErrors, delay=1, backoff=2, logger=getLogger(__name__))
def reserveLive(category: str, communityId: str, tags: List[str], session: Session) -> None:
    liveDict = generateLiveDict(category, communityId, tags)
    startTime = getStartTimeOfNextLive()
    duration = 360

    response = takeReservation(liveDict, startTime, duration, session)
    responseJson: dict = response.json()
    responseMeta: dict = responseJson.get("meta", {})
    if not responseMeta.get("status", 0) in [201, 400]:
        getLogger(__name__).error(
            "予約失敗/{0}".format(responseJson))
        response.raise_for_status()
        return
    elif responseMeta["status"] == 201:
        getLogger(__name__).info("予約完了/{0}".format(responseJson))
    elif responseMeta.get("errorCode", "") == "OVERLAP_MAINTENANCE":
        reserveLiveToGetOverMaintenance(liveDict, startTime, session)
    else:
        response.raise_for_status()


@retry(NetworkErrors, delay=1, backoff=2, logger=getLogger(__name__))
def getStartTime(liveId: str, session: Session) -> datetime:
    url = "https://live2.nicovideo.jp/unama/watch/{0}/programinfo"\
        .format(liveId)
    response = get(url, cookies=session.cookie)
    if response.status_code == 401:
        session.login()
        raise ReLoggedIn("ログインセッション更新。発生箇所:GST")
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
        raise ReLoggedIn("ログインセッション更新。発生箇所:GET")
    response.raise_for_status()
    result = response.json()
    beginUnixTime = int(result["data"]["endAt"])
    return datetime.fromtimestamp(beginUnixTime, timezone.utc)
