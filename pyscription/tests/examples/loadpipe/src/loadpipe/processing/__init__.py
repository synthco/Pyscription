
from typing import Iterable, Iterator

def identity(stream: Iterable[bytes]) -> Iterator[bytes]:
    for chunk in stream:
        yield chunk
