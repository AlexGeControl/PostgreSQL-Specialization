from datetime import datetime
from dateutil import parser


def _parse_mail_date(mail_date: str) -> str:
    pieces = mail_date.split()
    notz = " ".join(pieces[:4]).strip()

    # Try a bunch of format variations - strptime() is *lame*
    dnotz = None
    for form in [ 
        '%d %b %Y %H:%M:%S', 
        '%d %b %Y %H:%M:%S',
        '%d %b %Y %H:%M', 
        '%d %b %Y %H:%M', 
        '%d %b %y %H:%M:%S',
        '%d %b %y %H:%M:%S', 
        '%d %b %y %H:%M', 
        '%d %b %y %H:%M'
    ]:
        try:
            dnotz = datetime.strptime(notz, form)
            break
        except:
            continue

    if dnotz is None:
        return None

    iso = dnotz.isoformat()

    tz = "+0000"
    try:
        tz = pieces[4]
        if tz == '-0000' : tz = '+0000'
        tzh = tz[:3]
        tzm = tz[3:]
        tz = tzh+":"+tzm
    except:
        pass

    return iso+tz


def parse_mail_date(mail_date: str) :
    try:
        parse_mail_date = parser.parse(mail_date)
        return parse_mail_date.isoformat()
    except:
        return _parse_mail_date(mail_date)