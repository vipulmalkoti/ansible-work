# -*- coding: utf-8 -*-
"""Replace docker packages with container packages in ET cdn repos.

This module takes a file containing list of ET cdn repos seaparated by newline,
replaces package having `-docker` suffix with `-container` suffixed package,
and restores tags on new package. Optionally, it can also preserve the package
having `-docker` suffix, in that case the repo will have two packages, one
ending with `-docker` and another with `-container`.

Example:
    Replace `-docker` packages in all cdn repos listed in file cdn_repos.

        $ python replace-docker-packages.py cdn_repos

    Add `-container` package but do not replace the `-docker` package.

        $ python replace-docker-packages.py cdn_repos --append

    Remove `-docker` package

        $ python replace-docker-packages.py cdn_repos --clean

        WARNING: This option will remove `-docker` package from repo even if it
        is the only package in repo, so ensure repos have -container package
        before running clean.

Attributes:
    ET_HOST (str): URL of Errata instance to work on.
"""

import argparse
import json
import re

import requests
from requests_kerberos import HTTPKerberosAuth


ET_HOST = 'https://errata.devel.redhat.com'
#ET_HOST = 'https://errata.stage.engineering.redhat.com'


def get_repodata(reponame):
    """Call Errata's HTTP api to fetch packages list."""
    url = '%s/api/v1/cdn_repos/?filter[name]=%s' % (ET_HOST, reponame)
    res = requests.get(url, auth=HTTPKerberosAuth())
    res = res.json()
    package = res['data'][0]['relationships']['packages'][0]
    tags = [{'id': t['id'], 'template': t['tag_template']} for t in
            package['cdn_repo_package_tags']]
    for tag in tags:
        variant = get_tag_variant(tag['id'])
        tag['variant'] = variant
    package = {'id': package['id'], 'name': package['name']}
    return {'id': res['data'][0]['id'], 'package': package, 'tags': tags}


def get_tag_variant(tag_id):
    """Check if the tag is associated with a variant."""
    url = '%s/api/v1/cdn_repo_package_tags/%s' % (ET_HOST, tag_id)
    res = requests.get(url, auth=HTTPKerberosAuth())
    res = res.json()
    variant = res['data']['relationships'].get('variant')
    return variant


def replace_package(repo_id, new_package_name, old_package_name=None):
    """Overwrite package list for a repo."""
    url = '%s/api/v1/cdn_repos/%s' % (ET_HOST, repo_id)
    if old_package_name:
        package_names = [new_package_name, old_package_name]
    else:
        package_names = [new_package_name]
    data = {
        'cdn_repo': {
            'package_names': package_names
        }
    }
    res = requests.put(url, data=json.dumps(data), auth=HTTPKerberosAuth(),
                       headers={'Content-Type': 'application/json'})
    assert res.ok is True
    packages = res.json()['data']['relationships']['packages']
    for package in packages:
        if package['name'].endswith('-container'):
            return package['id']


def create_tag(tag, repo_id, package_id, variant_id=None):
    """Restore tag configuration from replaced package"""
    data = {
        'cdn_repo_package_tag': {
            'tag_template': tag,
            'cdn_repo_id': repo_id,
            'package_id': package_id
        }
    }
    if variant_id:
        data['cdn_repo_package_tag']['variant_id'] = variant_id
    url = '%s/api/v1/cdn_repo_package_tags' % ET_HOST
    res = requests.post(url, data=json.dumps(data),
                        auth=HTTPKerberosAuth(),
                        headers={'Content-Type': 'application/json'})
    assert res.ok is True


def main():
    """Start execution."""
    repodata = {}

    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Replace docker packages with container')
    parser.add_argument('repos', metavar='F', type=str,
                        help='File containing cdn repos separated by newline')
    parser.add_argument('--append', action='store_true',
                        default=False,
                        help='Append to package list instead of replacing.')
    parser.add_argument('--clean', action='store_true',
                        default=False,
                        help=('Remove docker package from repo. '
                              'Take care to only pass those repos that also '
                              'have container package, otherwise you are '
                              'gonna end up with empty repos.'))
    args = parser.parse_args()
    repolist_file = args.repos
    replace = False if args.append else True
    clean = args.clean

    # Collect existing packages with tags for each repo.
    with open(repolist_file, 'r') as f:
        for reponame in f:
            reponame = reponame.strip()
            repodata[reponame] = get_repodata(reponame)

    # Add new -container packages
    for repo in repodata:
        data = repodata[repo]
        package = data['package']
        package_name = package['name']
        if package_name.endswith('-docker'):
            new_package_name = re.sub('-docker$', '-container',
                                      package_name)
            if clean:
                replace_package(data['id'], new_package_name)
                # No need to add tags as container package already
                # exists in repo
                continue
            if replace:
                new_package_id = replace_package(data['id'], new_package_name)
            else:
                new_package_id = replace_package(data['id'], new_package_name,
                                                 package_name)
            for tag in data['tags']:
                # version-release is defined on all repos by default
                if tag['template'] == '{{version}}-{{release}}':
                    continue
                variant = tag.get('variant')
                variant_id = variant['id'] if variant else None
                create_tag(tag['template'], data['id'], new_package_id,
                           variant_id)


if __name__ == '__main__':
    main()
