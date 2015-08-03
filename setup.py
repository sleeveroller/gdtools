try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

config = {
	'name': 'gdtools',
	'description': 'Set of tools for Google Drive',
	'version': '0.1',
	'author': 'John Church',
	'author_email': 'sleeveroller@gmail.com',
	'url': 'https://github.com/sleeveroller/gdtools',
	'download_url': '',
        'long_description': open('README.rst').read(),
	'install_requires': [
		'nose',
		'PyDrive >= 1.0',
	],
	'packages': ['gdtools'],
	'scripts': [],
}

setup(**config)
