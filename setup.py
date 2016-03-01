from setuptools import setup

def read_file(f):
    with open(f) as f:
        return f.read()

setup(
    name='pear-aur',
    packages = ['pear'],
    version='0.9',
    description = 'A stupidly simple aur helper',
    long_description=read_file('README.rst'),
    author = 'Philip Dexter',
    author_email = 'philip.dexter@gmail.com',
    url = 'https://github.com/philipdexter/pear',
    download_url = 'https://github.com/philipdexter/pear/tarball/0.9',
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
