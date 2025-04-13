import sys
import os

# Make sure this runs before any Flask imports
import werkzeug
if not hasattr(werkzeug.urls, 'url_decode'):
    from werkzeug.urls import url_parse
    werkzeug.urls.url_decode = getattr(url_parse, 'url_decode', None)

# Similarly patch url_quote if needed
if not hasattr(werkzeug.urls, 'url_quote'):
    from werkzeug.urls import url_parse
    werkzeug.urls.url_quote = getattr(url_parse, 'url_quote', None)