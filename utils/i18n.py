import gettext

from config.settings import settings

_default_lang = "en"


def active_translation(lang: str):
    global _default_lang
    # TODO --> Order by 'q' beforehand
    try:
        for language in lang.split(","):
            if language[0:2] not in settings.SUPPORTED_LANGUAGE:
                continue
            _default_lang = language[0:2]
    except AttributeError:
        _default_lang = settings.DEFAULT_LANGUAGE


def trans(message: str) -> str:
    return gettext.translation(
        "base", localedir="locales", languages=[_default_lang]
    ).gettext(message)
