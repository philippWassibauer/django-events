from distutils.core import setup
import datetime

setup(name='django-events',
      version = datetime.datetime.strftime(datetime.datetime.now(), '%Y.%m.%d'),
      description='Events for django',
      long_description="Events for Django",
      author='Philipp Wassibauer',
      author_email='phil@maptales.com',
      url='http://github.com/philippWassibauer/django-events',
      packages=['events','events.templatetags'],
      package_data={'actstream':['events/templates/events/*.html']},
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Web Environment',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Utilities'],
      )
