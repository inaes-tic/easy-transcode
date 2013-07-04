from distutils.core import setup
import sys

sys.path.append('src')
sys.path.append('bin')

setup(name='mbc-transcode',
      version='0.1.0',
      author='Niv Sardi',
      author_email='xaiki@inaes.gob.ar',
      url='http://github.com/inaes-tic/easy-transcode',
      description='Easy Transcoding tool',
      package_dir={'': 'googlemaps'},
      py_modules=['googlemaps'],
      provides=['googlemaps'],
      keywords='google maps local search ajax api geocode geocoding directions navigation json',
      license='Lesser Affero General Public License v3',
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Intended Audience :: Developers',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 2',
                   'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
                   'License :: OSI Approved :: GNU Affero General Public License v3',
                   'Topic :: Internet',
                   'Topic :: Internet :: WWW/HTTP',
                   'Topic :: Scientific/Engineering :: GIS',
                  ],
     )
