import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-cml2',
    version='1.0.0.4',
    description='Application for data exchange in CommerceML 2 standard. This is a new version with new architecture',
    long_description=README,
    author='Sergey Grunenko',
    author_email='grunenko.serg@gmail.com',

    url='https://github.com/sergey-gru/django-cml2',
    license='BSD License',

    packages=['cml'],
    include_package_data=True,

    python_requires='>3.3.0',
    install_requires=['Django>=3.2', 'django-appconf>=1.0.1'],

    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 3.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
