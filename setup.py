# -*- coding: utf-8 -*-

"""reroils-app Invenio instance."""

import os

from setuptools import find_packages, setup
from setuptools.command.egg_info import egg_info


class EggInfoWithCompile(egg_info):
    def run(self):
        from babel.messages.frontend import compile_catalog
        compiler = compile_catalog()
        option_dict = self.distribution.get_option_dict('compile_catalog')
        if option_dict.get('domain'):
            compiler.domain = [option_dict['domain'][1]]
        else:
            compiler.domain = ['messages']
        compiler.use_fuzzy = True
        compiler.directory = option_dict['directory'][1]
        compiler.run()
        super().run()

# Get the version string. Cannot be done with import!
version = {}
with open(os.path.join('reroils_app',
                       'version.py'), 'rt') as fp:
    exec(fp.read(), version)

tests_require = [
    'check-manifest>=0.25',
    'coverage>=4.0',
    'isort>=4.2.2',
    'pydocstyle>=1.0.0',
    'pytest-cache>=1.0',
    'pytest-cov>=1.8.0',
    'pytest-pep8>=1.0.6',
    'pytest>=2.8.0'
]

extras_require = {
    'translations': [
        'transifex-client>=0.12.5'
    ],
    'tests': tests_require
}

extras_require['all'] = []
for reqs in extras_require.values():
    extras_require['all'].extend(reqs)

setup_requires = [
    'Babel>=1.3',
    'pytest-runner>=2.6.2',
]

setup(
    cmdclass={
        'egg_info': EggInfoWithCompile
    },
    name='reroils-app',
    version=version['__version__'],
    description=__doc__,
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'flask.commands': [
        ],
        'invenio_base.blueprints': [
            'reroils_app = '
            'reroils_app.views:blueprint',
        ],
        'invenio_config.module': [
            'reroils_app = '
            'reroils_app.config',
        ],
        'invenio_i18n.translations': [
            'messages = reroils_app',
        ],
        'invenio_assets.bundles': [
            'reroils_app_search_js = reroils_app.bundles:search_js',
        ],
    },
    extras_require=extras_require,
    setup_requires=setup_requires,
    tests_require=tests_require,
    install_requires=[
        'reroils_data>=0.1.0a1',
        'Flask>=0.11.1',
        'invenio-app>=1.0.0a1',
        'invenio-assets>=1.0.0a4',
        'invenio-base>=1.0.0a14',
        'invenio-config>=1.0.0b2',
        'invenio-db[postgresql]>=1.0.0a9',
        'invenio-indexer>=1.0.0a2',
        'invenio-jsonschemas>=1.0.0a5',
        'invenio-marc21>=1.0.0a1',
        'invenio-oaiserver>=1.0.0a1',
        'invenio-pidstore>=1.0.0a7',
        'invenio-records-rest>=1.0.0a11',
        'invenio-records-ui>=1.0.0a5',
        'invenio-search-ui>=1.0.0a4',
        'invenio-search>=1.0.0a7',
        'invenio-theme>=1.0.0a17',
        'invenio-celery>=1.0.0b3',
        'invenio-admin>=1.0.0b4',
        'SQLAlchemy-Utils<0.33.0'
    ],
)
