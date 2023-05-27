from dataclasses import dataclass


@dataclass
class Luxmed:
    email: str
    password: str


@dataclass
class LuxmedSniper:
    doctor_locator_id: str
    excluded_facilities: list[str]
    excluded_doctors: list[str]
    lookup_time_days: int
    notification_provider: list[str]


@dataclass
class Pushover:
    user_key: str
    api_token: str
    message_template: str
    title: str


@dataclass
class Slack:
    api_token: str
    channel: str
    message_template: str


@dataclass
class Pushbullet:
    access_token: str
    message_template: str
    title: str


@dataclass
class Misc:
    notifydb: str
    date_format: str


@dataclass
class Config:
    luxmed: Luxmed
    luxmedsniper: LuxmedSniper
    pushover: Pushover
    slack: Slack
    pushbullet: Pushbullet
    misc: Misc

    def __init__(self, **kwargs):
        self.luxmed = Luxmed(**kwargs['luxmed'])
        self.luxmedsniper = LuxmedSniper(**kwargs['luxmedsniper'])
        self.pushover = Pushover(**kwargs['pushover'])
        self.slack = Slack(**kwargs['slack'])
        self.pushbullet = Pushbullet(**kwargs['pushbullet'])
        self.misc = Misc(**kwargs['misc'])
