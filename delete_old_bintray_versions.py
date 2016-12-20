#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import base64
import httplib
import json
import os
import subprocess
import urllib2

def get_commit_hash(bintray_version):
    return bintray_version.split('-')[2].split('_')[0][1:]

def get_branch(bintray_version):
    return bintray_version[bintray_version.index('_') + 1:]

def get_branches(bintray_versions):
    return { get_branch(version) for version in bintray_versions }

def is_in_history(commit_id):
    with open(os.devnull, 'w') as null_handle:
        return_code = subprocess.call(['git', 'cat-file', 'commit', commit_id], stdout=null_handle, stderr=subprocess.STDOUT)

    return return_code == 0

def is_merged(commit_id, branch):
    branches = subprocess.check_output(['git', 'branch', '--contains', commit_id]).split('\n')

    return '  {}'.format(branch) in branches or '* {}'.format(branch) in branches

def get_branch_versions(bintray_versions, branch):
    return [ version for version in bintray_versions if get_branch(version) == branch ]

def get_default_branch(github_owner, github_repository, github_token):
    url = 'https://api.github.com/repos/{}/{}'.format(github_owner, github_repository)

    request = urllib2.Request(url)
    if github_token:
        request.add_header('Authorization', 'token {}'.format(github_token))

    return json.load(urllib2.urlopen(request))['default_branch']

def get_versions(user, repo, package):
    url = 'https://api.bintray.com/packages/{}/{}/{}'.format(user, repo, package)

    response = json.load(urllib2.urlopen(url))

    return response['versions'];

def get_delete_headers(user, api_token):
    credentials = '{}:{}'.format(user, api_token)
    return { 'Authorization': 'Basic {}'.format(base64.b64encode(credentials)) }

def delete_version(user, repo, package, version, api_token):
    print("Deleting from Bintray: {}".format(version))

    connection = httplib.HTTPSConnection('api.bintray.com')
    url_path = '/packages/{}/{}/{}/versions/{}'.format(user, repo, package, version)
    headers = get_delete_headers(user, api_token)

    connection.request('DELETE', url_path, None, headers)
    response = connection.getresponse()

    if response.status != 200:
        raise RuntimeError('Failed to delete version. Status: {}, reason: {}'.format(response.status, response.reason))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Delete old bintray versions')
    parser.add_argument('--github-owner', '-o', required = True)
    parser.add_argument('--github-repo', '-g', required = True)
    parser.add_argument('--bintray-user', '-u', required = True)
    parser.add_argument('--bintray-repo', '-b', required = True)
    parser.add_argument('--bintray-package', '-p', required = True)
    parser.add_argument('--bintray-token', '-t', required = True)
    parser.add_argument('--github-token', '-a')
    parser.add_argument('--num-versions-to-keep', '-n', required = True, type = int)

    arguments = parser.parse_args()

    versions = get_versions(arguments.bintray_user, arguments.bintray_repo, arguments.bintray_package)
    default_branch = get_default_branch(arguments.github_owner, arguments.github_repo, arguments.github_token)

    versions_to_delete = []
    versions_to_keep = []

    for branch in get_branches(versions):
        if branch == default_branch:
            continue

        branch_versions = get_branch_versions(versions, branch)
        commit_id = get_commit_hash(branch_versions[0])
        if not is_in_history(commit_id) or is_merged(commit_id, default_branch):
            versions_to_delete += branch_versions
        else:
            versions_to_keep.append(branch_versions[0])

    unprocessed_versions = [ version for version in versions if version not in versions_to_keep and version not in versions_to_delete ]

    first_old_version_index = arguments.num_versions_to_keep - len(versions_to_keep)
    if len(unprocessed_versions) > first_old_version_index:
        versions_to_delete += unprocessed_versions[first_old_version_index:]

    for version in versions_to_delete:
        delete_version(arguments.bintray_user, arguments.bintray_repo, arguments.bintray_package, version, arguments.bintray_token)
