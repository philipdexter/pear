import click
import json
import urllib.request
import tarfile
import os
import os.path
import subprocess
import operator
import tempfile
import sys

@click.group()
@click.version_option()
@click.pass_context
def cli(ctx):
    ctx.obj = {}
    pacman_output = subprocess.check_output(['pacman', '-Qm']).decode('utf-8')
    ctx.obj['packages'] = dict(map(lambda n: n.split(' '), pacman_output.strip().split('\n')))

@cli.command()
@click.argument('string')
def query(string):
    f = urllib.request.urlopen('https://aur.archlinux.org/rpc/?v=5&type=search&arg={}'.format(string))
    details = map(operator.itemgetter('Name', 'Version', 'Description'),
                  json.loads(f.read().decode('utf8'))['results'])
    formatted = map(lambda x: '{} - {}\n : {}\n----'.format(*x),
                    details)
    print('\n'.join(formatted))

def get_package(package):
    f = urllib.request.urlopen('https://aur.archlinux.org/rpc/?v=5&type=info&arg={}'.format(package))
    result = json.loads(f.read().decode('utf8'))
    packages = result['resultcount']
    if packages != 1:
        return None
    result = result['results'][0]
    return result

@cli.command()
@click.pass_context
@click.option('--ignore', multiple=True, help='Package to ignore')
def upgrade(ctx, ignore):
    local_packages = ctx.obj.get('packages', {}).items()
    if ignore:
        local_packages = list(filter(lambda x: x[0] not in ignore, local_packages))
    remote_packages = map(get_package, map(operator.itemgetter(0), local_packages))
    remote_package_versions = map(lambda x: x and x['Version'], remote_packages)
    for (n, lv), rv in zip(local_packages, remote_package_versions):
        if rv is None:
            print('failed to find {} on server'.format(n))
            continue
        elif lv != rv:
            print('found new version {} (old: {}) for {}, do you want to upgrade? [Y/n] '.format(rv, lv, n), end='')
            sys.stdout.flush()
            answer = sys.stdin.readline().strip()
            if answer in ('', ' ', 'Y', 'y'):
                print('upgrading {} from {} to {}'.format(n, lv, rv))
                install(ctx, n)
            else:
                print('skipping upgrading {} from {} to {}'.format(n, lv, rv))
        else:
            print('{} is up to date'.format(n))
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
        f = urllib.request.urlopen('https://aur.archlinux.org/{}'.format(result['URLPath']))
        current_path = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
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
            os.chdir(current_path)

        packages = ctx.obj.get('packages', {})
        pkg = result['Name']
        version = result['Version']
        pkg_version = packages.get(pkg)
        if pkg_version != version:
            packages[pkg] = version

@cli.command(name='install')
@click.argument('packages', nargs=-1)
@click.pass_context
def install_cli(ctx, packages):
    for p in packages:
        print('installing {}'.format(p))
        install(ctx, p)
