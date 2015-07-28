import click
import json
import urllib.request
import tarfile
import os
import os.path
import subprocess
import operator

_config_file = os.path.expanduser('~/.pear')

@click.group()
@click.version_option()
@click.pass_context
def cli(ctx):
    ctx.obj = {}
    if not os.path.isfile(_config_file):
        with open(_config_file, 'a'):
            pass
    with open(_config_file, 'r') as f:
        contents = f.read().strip()
    try:
        ctx.obj['packages'] = dict(map(lambda x: x.strip().split(' '), contents.split('\n')))
    except ValueError:
        pass

@cli.command()
@click.argument('string')
def query(string):
    f = urllib.request.urlopen('https://aur4.archlinux.org/rpc.php?type=search&arg={}'.format(string))
    details = map(operator.itemgetter('Name', 'Version', 'Description'),
                  json.loads(f.read().decode('utf8'))['results'])
    formatted = map(lambda x: '{} - {}\n : {}\n----'.format(*x),
                    details)
    print('\n'.join(formatted))

@cli.command()
@click.argument('package')
@click.pass_context
def install(ctx, package):
    f = urllib.request.urlopen('https://aur4.archlinux.org/rpc.php?type=info&arg={}'.format(package))
    result = json.loads(f.read().decode('utf8'))
    packages = result['resultcount']
    if packages > 1:
        print('error: multiple packages found')
    elif packages == 0:
        print('error: no packages found')
    else:
        result = result['results']
        print(result['URLPath'])
        f = urllib.request.urlopen('https://aur4.archlinux.org/{}'.format(result['URLPath']))
        tar_file = '{}.tar.gz'.format(result['Name'])
        directory = '{}'.format(result['Name'])
        with open(tar_file, 'wb') as out:
            out.write(f.read())
        tar = tarfile.open(tar_file)
        tar.extractall()
        tar.close()
        with open('{}/PKGBUILD'.format(directory)) as f:
            for line in f:
                if line.startswith('depends='):
                    line = line.strip().split('=')[1].strip('()').split(' ')
                    print('dependencies: {}'.format(' '.join(line)))
        os.chdir(directory)
        subprocess.call(['makepkg', '-s', '-i'])
        os.chdir('..')
    packages = ctx.obj.get('packages', {})
    pkg = result['Name']
    version = result['Version']
    pkg_version = packages.get(pkg)
    print(pkg, version, pkg_version)
    if pkg_version != version:
        packages[pkg] = version
    contents = map(lambda x: '{} {}'.format(x, packages[x]), list(packages))
    with open(_config_file, 'w') as f:
        f.write('\n'.join(contents) + '\n')
