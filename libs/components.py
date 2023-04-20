import datetime


def time_left(timestamp: int) -> str:
    date = datetime.datetime.fromtimestamp(timestamp)
    date = date.replace(second=0, microsecond=0)
    if date.second >= 30:
        date += datetime.timedelta(minutes=1)

    time_left = date - datetime.datetime.now()
    total_seconds = int(time_left.total_seconds())
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    if days > 0:
        description = "{}d,{}h,{}m".format(days, hours, minutes)
    elif hours > 0:
        description = "{}h,{}m".format(hours, minutes)
    else:
        description = "{}m".format(minutes)
    return description