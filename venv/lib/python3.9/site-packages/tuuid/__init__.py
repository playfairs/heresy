# MIT License

# Copyright (c) 2022 Montel Edwards

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import threading
import time
from datetime import datetime
from typing import Optional, Union

from ._hashids import Hashids

_hashids = Hashids()
_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
_tuuid_lock = threading.Lock()


def from_datetime(datetime: datetime) -> str:
    """Generate tuuid from datetime

    Args:
        datetime (datetime)

    Returns:
        str
    """
    return _hashids.decode(int(datetime.timestamp()))


def from_ts(timestamp: Union[float, int]) -> str:
    """Generate tuuid from timestamp

    Args:
        timestamp Union[float, int]

    Returns:
        str
    """

    return _hashids.decode(int(timestamp))


def tuuid() -> str:
    """Generate a timstamp based hashid.
    Utilizes a mutex to ensure hashes are unique.

    Returns:
        str: the tuuid
    """
    with _tuuid_lock:

        return _hashids.encode(time.time_ns())


def decode(tuuid: str, return_type: Optional[str] = "date") -> Union[datetime, int]:
    """Decode a tuuid to Timestamp or datetime.dateimte

    Args:
        tuuid (str): A tuuid generated from tuuid.random()
        return_type (Optional[str], optional): Return type. Options  of 'date' or 'ts'. Defaults to "date".

    Returns:
        Union[datetime, int]: Decoded hashid
    """

    hashid_decoded = _hashids.decode(tuuid)[0]
    times = hashid_decoded / 1000000000

    timestamp = int(times)
    if return_type == "date":
        return datetime.fromtimestamp(timestamp)

    if return_type in ("ts", "timestamp"):
        return timestamp
