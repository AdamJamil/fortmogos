class MissingTimezoneException(Exception):
    help = (
        "Please report your timezone first! Report one of the following: "
        "the current time in your area `timezone 4:20PM`; the offset "
        "`timezone UTC+5`; the region name `timezone US/Eastern`."
    )
