"""
This file is part of the Requests library and is distributed under the Apache License 2.0.
For licensing details, refer to `structures.LICENSE` and `structures.NOTICE`.
Note that this file has been modified from its original version.
"""

from collections.abc import Mapping, MutableMapping
from typing import Iterator


class CaseInsensitiveDict[V_T](MutableMapping[str, V_T]):
    """A case-insensitive ``dict``-like object.

    Implements all methods and operations of
    ``MutableMapping`` as well as dict's ``copy``. Also
    provides ``lower_items``.

    All keys are expected to be strings. The structure remembers the
    case of the last key to be set, and ``iter(instance)``,
    ``keys()``, ``items()``, ``iterkeys()``, and ``iteritems()``
    will contain case-sensitive keys. However, querying and contains
    testing is case insensitive::

        cid = CaseInsensitiveDict()
        cid['Accept'] = 'application/json'
        cid['aCCEPT'] == 'application/json'  # True
        list(cid) == ['Accept']  # True

    For example, ``headers['content-encoding']`` will return the
    value of a ``'Content-Encoding'`` response header, regardless
    of how the header name was originally stored.

    If the constructor, ``.update``, or equality comparison
    operations are given keys that have equal ``.lower()``s, the
    behavior is undefined.
    """

    def __init__(self, data=None, /, **kwargs):
        self.__store: dict[str, tuple[str, V_T]] = {}
        if data is not None:
            self.update(data)
        if kwargs:
            self.update(kwargs)

    def __setitem__(self, key: str, value: V_T):
        # Uses lowercase key for lookup and stores the cased key
        self.__store[key.lower()] = (key, value)

    def __getitem__(self, key: str) -> V_T:
        # Uses lowercase key for lookup
        return self.__store[key.lower()][1]

    def __delitem__(self, key: str):
        # Uses lowercase key for lookup
        del self.__store[key.lower()]

    def __iter__(self) -> Iterator[str]:
        # Returns cased keys
        return (k for k, _ in self.__store.values())

    def __len__(self) -> int:
        return len(self.__store)

    def lower_items(self) -> Iterator[tuple[str, V_T]]:
        # Like items(), but with lowercase keys.
        return ((k, v[1]) for k, v in self.__store.items())

    def __eq__(self, other):
        # Compares lowercase keys and values
        if not isinstance(other, Mapping):
            return NotImplemented

        if not isinstance(other, CaseInsensitiveDict):
            other = CaseInsensitiveDict(other)

        return dict(self.lower_items()) == dict(other.lower_items())

    def __or__(self, other) -> "CaseInsensitiveDict[V_T]":
        if not isinstance(other, Mapping):
            return NotImplemented

        new = CaseInsensitiveDict(self)
        new.update(other)
        return new

    def __ior__(self, other) -> "CaseInsensitiveDict[V_T]":
        if not isinstance(other, Mapping):
            return NotImplemented

        self.update(other)
        return self

    def copy(self) -> "CaseInsensitiveDict[V_T]":
        return CaseInsensitiveDict(self)

    def __repr__(self) -> str:
        return f"CaseInsensitiveDict({repr(dict(self.items()))})"
