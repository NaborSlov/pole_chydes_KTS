from dataclasses import dataclass, field
import marshmallow


@dataclass
class GetUpdates:
    ok: bool
    result: list["Updates"] = field(default_factory=list)


@dataclass
class Updates:
    update_id: int
    message: "Message" = None
    callback_query: "CallbackQuery" = None
    poll_answer: "PollAnswer" = None

    class Meta:
        unknown = marshmallow.EXCLUDE


@dataclass
class PollAnswer:
    user: "From"
    poll_id: int
    option_ids: list[int] = field(default_factory=list)

    class Meta:
        unknown = marshmallow.EXCLUDE


@dataclass
class CallbackQuery:
    id: str
    from_: "From" = field(metadata={"data_key": "from"})
    data: str

    class Meta:
        unknown = marshmallow.EXCLUDE


@dataclass
class Message:
    message_id: int
    from_: "From" = field(metadata={"data_key": "from"})
    chat: "Chat"
    date: int
    text: str = ""

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
    reply_markup: dict = field(default_factory=dict)


@dataclass
class InlineKeyboardButton:
    text: str
    callback_data: str


@dataclass
class InlineKeyboardMarkup:
    inline_keyboard: list[list] = field(default_factory=list[list])


@dataclass
class ReplyKeyboardMarkup:
    keyboard: list[list] = field(default_factory=list[list])


@dataclass
class KeyboardButton:
    text: str


@dataclass
class SendPoll:
    chat_id: int
    question: str
    options: list[str] = field(default_factory=list)
    is_anonymous: bool = False
    open_period: int = 180
