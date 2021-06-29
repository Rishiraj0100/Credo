from tortoise.fields.base import Field
from typing import Any
from datetime import datetime

__all__ = (
    "ArrayField",
    "TimeWithoutTimeZoneField"
)
# Those fields were redundant its time to use this.
class ArrayField(Field, list):
    def __init__(self, field: Field, **kwargs) -> None:
        super().__init__(**kwargs)
        self.sub_field = field
        self.SQL_TYPE = "%s[]" % field.SQL_TYPE

    def to_python_value(self, value: Any) -> Any:
        return list(map(self.sub_field.to_python_value, value))

    def to_db_value(self, value: Any, instance: Any) -> Any:
        return [self.sub_field.to_db_value(val, instance) for val in value]

class TimeWithoutTimeZoneField(Field,str):
    SQL_TYPE = "time without time zone"

    def to_db_value(self, value: Any):
        time = datetime.strptime(value,'%H:%M')
        main_time = time.time()
        return main_time

    def to_python_value(self, value: Any):
        return value
