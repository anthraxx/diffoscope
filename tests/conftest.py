import diffoscope
import pytest

set_locale = pytest.fixture(autouse=True, scope='session')(diffoscope.set_locale)
