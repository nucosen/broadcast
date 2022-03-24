from logging import getLogger
from random import randint, shuffle
from typing import List, Optional

from requests import get
from requests.exceptions import ConnectionError, HTTPError
from retry import retry


class RetryRequested(Exception):
    pass


NetworkErrors = (HTTPError, ConnectionError, RetryRequested)


def choiceFromRequests(requests: List[str], max: int) -> Optional[List[str]]:
    shuffle(requests)
    winner = list()
    for request in requests:
        if request in winner:
            continue
        winner.append(request)
        if len(winner) >= max:
            break
    return winner if len(winner) else None


@retry(NetworkErrors, delay=1, backoff=2, logger=getLogger(__name__))
def randomSelection(tags: List[str]) -> str:
    url = "https://api.search.nicovideo.jp/api/v2/snapshot/video/contents/search"
    header = {
        "UserAgent": "NUCOSen Broadcast Personality System"
    }
    shuffle(tags)
    payload = {
        "q": tags.pop(),
        "targets": "tagsExact",
        "fields": "contentId",
        "filters[lengthSeconds][gte]": 45,
        "filters[lengthSeconds][lte]": 10 * 60,
        "_sort": "-lastCommentTime",
        "_context": "NUCOSen backend",
        "_limit": "10",
        "_offset": randint(0, 90)
    }

    ngmovies = [
        "sm30122129"
    ]

    response = get(url, headers=header, params=payload)
    result = dict(response.json())
    response.raise_for_status()
    winner: List[str] = []
    for target in result['data']:
        if not target["contentId"] in ngmovies:
            winner.append(target['contentId'])
    shuffle(winner)
    if len(winner) == 0:
        raise RetryRequested("再抽選中…。オフセット値を調整する必要があるかもしれません。")
    return winner.pop()
