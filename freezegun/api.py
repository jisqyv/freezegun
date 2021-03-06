import datetime
import functools

from dateutil import parser

real_date = datetime.date
real_datetime = datetime.datetime


class FakeDate(real_date):
    active = False
    date_to_freeze = None

    def __new__(cls, *args, **kwargs):
        return real_date.__new__(real_date, *args, **kwargs)

    @classmethod
    def today(cls):
        if cls.active:
            return cls.date_to_freeze
        else:
            return real_date.today()


class FakeDatetime(real_datetime):
    active = False
    time_to_freeze = None
    tz_offset = None

    def __new__(cls, *args, **kwargs):
        return real_datetime.__new__(real_datetime, *args, **kwargs)

    @classmethod
    def now(cls):
        if cls.active:
            return cls.time_to_freeze + datetime.timedelta(hours=cls.tz_offset)
        else:
            return real_datetime.now()

    @classmethod
    def utcnow(cls):
        if cls.active:
            return cls.time_to_freeze
        else:
            return real_datetime.utcnow()

datetime.datetime = FakeDatetime
datetime.date = FakeDate


class _freeze_time():

    def __init__(self, time_to_freeze_str, tz_offset):
        time_to_freeze = parser.parse(time_to_freeze_str)

        self.time_to_freeze = time_to_freeze
        self.tz_offset = tz_offset

    def __call__(self, func):
        return self.decorate_callable(func)

    def __enter__(self):
        self.start()

    def __exit__(self, *args):
        self.stop()

    def start(self):
        datetime.datetime.time_to_freeze = self.time_to_freeze
        datetime.datetime.tz_offset = self.tz_offset
        datetime.datetime.active = True

        # Since datetime.datetime has already been mocket, just use that for
        # calculating the date
        datetime.date.date_to_freeze = datetime.datetime.now().date()
        datetime.date.active = True

    def stop(self):
        datetime.datetime.active = False
        datetime.date.active = False

    def decorate_callable(self, func):
        def wrapper(*args, **kwargs):
            with self:
                result = func(*args, **kwargs)
            return result
        functools.update_wrapper(wrapper, func)
        return wrapper


def freeze_time(time_to_freeze, tz_offset=0):
    return _freeze_time(time_to_freeze, tz_offset)
