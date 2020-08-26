"""Provides utility functions for internationalization (i18n).

While Django already provides several functions for internationalization aswell
as localization (l10n), there are no money/currency related functions.

`stockings` relies on `Babel` to fill this gap. The functions provided in this
module should provide an interface between `Django` and `Babel`, where
necessary.
"""

# Django imports
from django.conf import settings
from django.utils.translation import get_language, to_locale


def get_current_locale():
    """Convert the currently active language to a locale to be used by Babel.

    Returns
    -------
    locale : str

    Warnings
    --------
    This function may be called several times (per request), which may be highly
    inefficient. Probably there is a cleaner way to cache the result for one
    request.
    """
    language = get_language() or settings.LANGUAGE_CODE
    locale = to_locale(language)

    return locale
