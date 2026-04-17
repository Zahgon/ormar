# inspired by sqlalchemy-utils (https://github.com/kvesteri/sqlalchemy-utils)
import abc
import base64
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Optional, Union

import sqlalchemy.types as types
from sqlalchemy.engine import Dialect

import ormar  # noqa: I100, I202
from ormar import ModelDefinitionError  # noqa: I202, I100
from ormar.fields.parsers import ADDITIONAL_PARAMETERS_MAP

cryptography = None
try:  # pragma: nocover
    import cryptography  # type: ignore
    from cryptography.fernet import Fernet
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
except ImportError:  # pragma: nocover
    pass

if TYPE_CHECKING:  # pragma: nocover
    from ormar import BaseField


class EncryptBackend(abc.ABC):
    def _refresh(self, key: Union[str, bytes]) -> None:
        pass

    @abc.abstractmethod
    def _initialize_backend(self, secret_key: bytes) -> None:  # pragma: nocover
        pass

    @abc.abstractmethod
    def encrypt(self, value: Any) -> str:  # pragma: nocover
        pass

    @abc.abstractmethod
    def decrypt(self, value: Any) -> str:  # pragma: nocover
        pass


class HashBackend(EncryptBackend):
    """
    One-way hashing - in example for passwords, no way to decrypt the value!
    """

    def _initialize_backend(self, secret_key: bytes) -> None:
        pass

    def encrypt(self, value: Any) -> str:
        pass

    def decrypt(self, value: Any) -> str:
        pass


class FernetBackend(EncryptBackend):
    """
    Two-way encryption, data stored in db are encrypted but decrypted during query.
    """

    def _initialize_backend(self, secret_key: bytes) -> None:
        pass

    def encrypt(self, value: Any) -> str:
        pass

    def decrypt(self, value: Any) -> str:
        pass


class EncryptBackends(Enum):
    NONE = 0
    FERNET = 1
    HASH = 2
    CUSTOM = 3


BACKENDS_MAP = {
    EncryptBackends.FERNET: FernetBackend,
    EncryptBackends.HASH: HashBackend,
}


class EncryptedString(types.TypeDecorator):
    """
    Used to store encrypted values in a database
    """

    impl = types.TypeEngine

    cache_ok = True

    def __init__(
        self,
        encrypt_secret: Union[str, Callable],
        encrypt_backend: EncryptBackends = EncryptBackends.FERNET,
        encrypt_custom_backend: Optional[type[EncryptBackend]] = None,
        **kwargs: Any,
    ) -> None:
        _field_type = kwargs.pop("_field_type")
        super().__init__()
        if not cryptography:  # pragma: nocover
            raise ModelDefinitionError(
                "In order to encrypt a column 'cryptography' is required!"
            )
        backend = BACKENDS_MAP.get(encrypt_backend, encrypt_custom_backend)
        if (
            not backend
            or not isinstance(backend, type)
            or not issubclass(backend, EncryptBackend)
        ):
            raise ModelDefinitionError("Wrong or no encrypt backend provided!")

        self.backend: EncryptBackend = backend()
        self._field_type: "BaseField" = _field_type
        self._underlying_type: Any = _field_type.column_type
        self._key: Union[str, Callable] = encrypt_secret
        type_ = self._field_type.__type__
        if type_ is None:  # pragma: nocover
            raise ModelDefinitionError(
                f"Improperly configured field {self._field_type.name}"
            )
        self.type_: Any = type_

    def __repr__(self) -> str:  # pragma: nocover
        return "TEXT()"

    def load_dialect_impl(self, dialect: Dialect) -> Any:
        pass

    def _refresh(self) -> None:
        pass

    def process_bind_param(self, value: Any, dialect: Dialect) -> Optional[str]:
        pass

    def process_result_value(self, value: Any, dialect: Dialect) -> Any:
        pass

    def _get_coder_type_and_params(
        self, coders: dict[type, Callable]
    ) -> tuple[Optional[Callable], Optional[str]]:
        pass
