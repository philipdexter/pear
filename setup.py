from setuptools import setup

setup(
    name='pear',
    packages = ['pear'],
    version='0.1',
    description = 'A stupidly simple aur helper',
    author = 'Philip Dexter',
    author_email = 'philip.dexter@gmail.com',
    url = 'https://github.com/philipdexter/pear',
    download_url = 'https://github.com/philipdexter/pear/tarball/0.1',
    keywords = ['aur', 'arch linux'],
    classifiers = [],
    license = 'Unlicense',
    py_modules=['pear'],
    include_package_data=True,
    install_requires=[
        'click',
    ],
    entry_points='''
        [console_scripts]
        pear=pear:cli
    ''',
)
