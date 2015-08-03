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

def get_package(package):
    f = urllib.request.urlopen('https://aur4.archlinux.org/rpc.php?type=info&arg={}'.format(package))
    result = json.loads(f.read().decode('utf8'))
    packages = result['resultcount']
    if packages != 1:
        return None
    result = result['results']
    return result

@cli.command()
@click.pass_context
def upgrade(ctx):
    local_packages = ctx.obj.get('packages', {}).items()
    remote_packages = map(get_package, map(operator.itemgetter(0), local_packages))
    remote_package_versions = map(operator.itemgetter('Version'), remote_packages)
    for (n, lv), rv in zip(local_packages, remote_package_versions):
        print(n, lv, rv)
        if lv != rv:
            print('upgrading {} from {} to {}'.format(n, lv, rv))
            install(ctx, n)
    print('done')


@cli.command(name='list')
@click.pass_context
def listpackages(ctx):
    local_packages = sorted(ctx.obj.get('packages', {}).items(), key=operator.itemgetter(0))
    for p, v in local_packages:
        print(p, v)

def install(ctx, package):
    result = get_package(package)
    if result is None:
        print('error: no single package found')
    else:
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
        if pkg_version != version:
            packages[pkg] = version
        contents = map(lambda x: '{} {}'.format(x, packages[x]), list(packages))
        with open(_config_file, 'w') as f:
            f.write('\n'.join(contents) + '\n')

@cli.command(name='install')
@click.argument('package')
@click.pass_context
def install_cli(ctx, package):
    install(ctx, package)
