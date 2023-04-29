===
CML
===

CML is a reusable Django app for data exchange in CommerceML 2 standard.

This packet is avaliable here: https://pypi.org/project/django-cml2


Requirements
------------

- Python 3.3, 3.4, 3.5, 3.6
- Django 3.2

Quick start
-----------

1. Install using pip::

    pip install django-cml2

   or clone the repo and add to your `PYTHONPATH`::

    git clone https://github.com/sergey-gru/django-cml2.git


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


Release notes
----------------
- 1.0.0 This version was created based on https://github.com/ArtemiusUA/django-cml
