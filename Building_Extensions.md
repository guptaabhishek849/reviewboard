This page is out of date. The current documentation for building extensions can be found at [Writing Review Board Extensions](http://www.reviewboard.org/docs/codebase/dev/extending/extensions/).

# Introduction #

This is the beginnings of a guide to building review board extensions.

## Basic Skeleton ##
  * `setup.py`
```
from setuptools import setup, find_packages

PACKAGE = "SampleExtension"
VERSION = "0.1"

setup(
    name=PACKAGE,
    version=VERSION,
    description="description of extension",
    author="Your Name",
    packages=["sample_extension"],
    entry_points={
        'reviewboard.extensions':
            '%s = sample_extension.extension:SampleExtension' % PACKAGE,
    },
)
```
> If you have static files that need to be copied over, define them in the package\_data entry:
```
    package_data={
        'sample_extension': [
            'templates/sample_extension/*.html',
        ],
    },
```
  * `sample_extension/__init__.py`
  * `sample_extension/extension.py`
```
from django.conf import settings
from django.conf.urls.defaults import patterns, include
from reviewboard.extensions.base import Extension

class SampleExtension(Extension):
    def __init__(self, *args, **kwargs):
        super(SampleExtension, self).__init__()
```

## Adding a Configuration Page ##
  * `sample_extension/extension.py`
> Add the following line to the SampleExtension class definition.
```
    is_configurable = True
```
  * `sample_extension/admin_urls.py`
> Ensure that the empty pattern is matched at a minimum, as that will be the default configuration location:
```
patterns('sample_extension.views',
    url(r'^$', 'configure'),
)
```
  * `sample_extension/views.py`
> Define the configuration view specified in the `admin_urls.py` pattern.
  * `sample_extension/templates/*.html`

## Adding a Dashboard Link ##
  * `sample_extension/urls.py`
> Ensure that the empty pattern is matched at a minimum, as that will be the location of the dashboard link:
```
patterns('sample_extension.views',
    url(r'^$', 'dashboard'),
)
```
  * `sample_extension/extension.py`
> Two hooks need to be defined to support the dashboard hook: a `URLHook`, and a `DashboardHook`:
```
from reviewboard.extensions.base import Extension
from reviewboard.extensions.hook import DashboardHook, URLHook
```
```
class SampleExtensionURLHook(URLHook):
    def __init__(self, extension, *args, **kwargs):
        pattern = patterns('', (r'^sample_extension_path/',
                           include('sample_extension.urls')))
        super(SampleExtensionURLHook, self).__init__(extension, pattern)

        
class SampleExtensionDashboardHook(DashboardHook):
    def __init__(self, extension, *args, **kwargs):
        entries = [{
            'label': '<name of sidebar link>',
            'url': settings.SITE_ROOT + 'sample_extension_path/',
        }]
        super(SampleExtensionDashboardHook, self).__init__(extension,
                entries=entries, *args, **kwargs)
```
> They will then need to be assigned to members of the Extension during initialization.
```
        self.url_hook = SampleExtensionURLHook(self)
        self.dashboard_hook = SampleExtensionDashboardHook(self)
```
  * `sample_extension/views.py`
> Define the dashboard view specified in the `urls.py` pattern.

## Adding a Template Hook ##
  * `sample_extension/extension.py`
> Another hook will need to be defined to support the template hook. Add an import for `TemplateHook` to the existing Hook imports:
```
from reviewboard.extensions.hook import DashboardHook, URLHook, TemplateHook
```
> Then add the hook to the existing 'SampleExtension' class:
```
class SampleExtension(Extension):
    is_configurable = True
    def __init__(self, *args, **kwargs):
        super(SampleExtension, self).__init__()
        self.url_hook = SampleExtensionURLHook(self)
        self.dashboard_hook = SampleExtensionDashboardHook(self)
        self.template_hook = TemplateHook(self, "template-hook-label",
            "SampleExtension/template.html", [
                'context1',
                'context2',
                'context3',
            ]
        )
```
> To explain this a bit, you are instantiating and holding reference to a TemplateHook. This passes four parameters when instantiating. First it is passed the extension calling it (self), then the name of the hook point (template-hook-label) which are already present in the reviewboard templates. Next it is passed the extension template to invoke at this hook point. Finally it can be passed an optional array of contexts that the hook will be activated on. These contexts are mapped to names already defined within the urls.py file.

# Storing to the database #

## Configuration Settings ##

The djblets extension base class, Extension, provides a settings member. This member is a "glorified dictionary" which can be saved to, and loaded from the database.

  * Example 1 - Loading Settings
```
ExtensionName.settings.load()
mysetting = ExtensionName.settings['mysetting']
```
  * Example 2 - Saving Settings
```
ExtensionName.settings['mysetting'] = "New Setting Value"
ExtensionName.settings.save()
```

## Models ##

When an extension is loaded, it is added to the django INSTALLED\_APPS automatically. New models are written to the database by review board by running syncdb programmatically (This is done for you).

# Relevant Links #

  * Some simple toy extensions - https://github.com/mikeconley/RB-Toy-Extensions
  * Extension to enhance bug tracker support - https://github.com/hongbin/rb-extension-pack/tree/bug-tracker
  * Blog post outlining how extensions make db changes, and use python eggs - http://mikeconley.ca/blog/2010/05/12/python-eggs-sunny-side-up-and-other-goodies/