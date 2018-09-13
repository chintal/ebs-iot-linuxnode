import setuptools

_requires = [
    'six',
    'setuptools-scm',
    'appdirs',
    'Cython',
    'twisted[tls]',
    'SQLAlchemy',
    'kivy>1.10.1',

    # Node Id
    'netifaces',

    # BleedImage
    'colorthief',
    
    # HTTP Client
    'treq',

    # Event Manager
    'cached_property',
    'pqueue'
]

setuptools.setup(
    name='ebs-iot-linuxnode',
    url='',

    author='Chintalagiri Shashank',
    author_email='shashank.chintalagiri@gmail.com',

    description='',
    long_description='',

    packages=setuptools.find_packages(),
    package_dir={'ebs.iot.linuxnode': 'ebs/iot/linuxnode'},
    package_data={'ebs.iot.linuxnode': ['images/no-internet.png',
                                        'images/no-server.png']},

    install_requires=_requires,
    dependency_links=[
        'git+https://github.com/kivy/kivy.git@master#egg=kivy-1.11.0'
    ],

    setup_requires=['setuptools_scm'],
    use_scm_version=True,

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Operating System :: POSIX :: Linux',
    ],
)
