import json
from datetime import datetime

# str = "[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]"
# l = json.loads(str)
# print(l)
# print(type(l))

date_format = '%Y-%m-%d %H:%M:%S'

_dt = datetime.strptime('2018-10-02 01:00:00', date_format)
year, month, day, hour, minute, is_weekday ,is_wod = _dt.year, _dt.month, _dt.day, _dt.hour, _dt.minute, _dt.weekday() ,_dt.isoweekday()
print("aaaa")