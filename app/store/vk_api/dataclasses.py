from dataclasses import dataclass, field
import marshmallow


@dataclass
class GetUpdates:
    ok: bool
    result: list["Updates"] = field(default_factory=list)


@dataclass
class Updates:
    update_id: int
    message: "Message"

    class Meta:
        unknown = marshmallow.EXCLUDE


@dataclass
class Message:
    message_id: int
    from_: "From" = field(metadata={"data_key": "from"})
    chat: "Chat"
    date: int
    text: str

    class Meta:
        unknown = marshmallow.EXCLUDE


@dataclass
class From:
    id: int
    first_name: str = ""
    username: str = ""

    class Meta:
        unknown = marshmallow.EXCLUDE


@dataclass
class Chat:
    id: int
    first_name: str = ""
    username: str = ""

    class Meta:
        unknown = marshmallow.EXCLUDE


@dataclass
class SendMessage:
    chat_id: int
    text: str
