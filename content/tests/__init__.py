# This file makes the tests directory a Python package 

from .test_templates import TemplateTests
from .test_social_features import SocialFeaturesTests
from .test_search import SearchTests
from .test_javascript import JavaScriptTests
from .test_media import MediaTests
from .test_ui import UITests
from .test_landing import LandingPageTests
from .test_posts import PostTests

__all__ = [
    'TemplateTests',
    'SocialFeaturesTests',
    'SearchTests',
    'JavaScriptTests',
    'MediaTests',
    'UITests',
    'LandingPageTests',
    'PostTests',
] 