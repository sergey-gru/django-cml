===
CML
===

CML is a reusable Django app for data exchange in CommerceML 2 standard.

This packet is available here: https://pypi.org/project/django-cml2


Requirements
------------

- Python 3.3, 3.4, 3.5, 3.6
- Django 3.2

Quick start
-----------

1. Install using pip::

    pip install django-cml2

   or clone the repo and add to your virtual environment `venv`::

    # cd <your_project>
    # source venv/bin/activate

    git clone https://github.com/sergey-gru/django-cml2.git
    pip install --editable django-cml2


2. Add 'cml' to your `settings.py` like this::

    INSTALLED_APPS = [
        ...
        'cml',
    ]

3. Include the cml URLconf in your project `urls.py` like this::

    urlpatterns = [
        ...
        path('cml', include('cml.urls')),
    ]

4. To create cml models run::

    python manage.py migrate cml


5. Create a template of `cml_delegate.py`::

    python manage.py cml_init

6. Register it to `settings.py` file like this::

    CML_USER_DELEGATE = 'cml_delegate'
    # CML_USER_DELEGATE = 'app.cml_delegate'

7. Modify methods to stack new cml packet with your django models.


8. Add logger settings to your `settings.py`::

    LOGGING = {
        'version': 1,
        ...

        'handlers': {
            'console': {...},
            'log_debug': {...},
            'log_info': {...},
        },

        'loggers': {
            ...

            # Logging important change process
            'cml.views': {
                'handlers': ['console', 'log_debug', 'log_info'] if DEBUG else ['log_info'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'cml.utils': {
                'handlers': ['console', 'log_debug', 'log_info'] if DEBUG else ['log_info'],
                'level': 'INFO',
                'propagate': False,
            },
        }
    }

Release notes
----------------
- 1.0.0 This version was forked from https://github.com/ArtemiusUA/django-cml
