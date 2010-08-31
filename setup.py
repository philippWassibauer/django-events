from distutils.core import setup

setup(name='django-events',
      version="0.1",
      description='Events for django',
      long_description=open('README.rst').read(),
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
