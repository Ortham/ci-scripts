#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Remove artifacts for all Git branches that don't currently exist.
# Also remove artifacts for the current branch, so that each branch only ever
# has at most one build's artifacts hosted.

import argparse
import json
import urllib.parse
from urllib.request import Request, urlopen

# This doesn't support pagination, so won't return a complete list for repositories with many branches.
def get_existing_branches(github_repo, github_token):
    url = 'https://api.github.com/repos/{}/branches'.format(github_repo)
    headers = { 'Authorization': 'token {}'.format(github_token) }

    request = Request(url)
    if github_token:
        request.add_header('Authorization', 'token {}'.format(github_token))

    response_body = json.load(urlopen(request))

    return [branch['name'] for branch in response_body]

def transform_branch_name(name):
    return  urllib.parse.quote(name, safe='')

def transform_branch_names(names):
    return [transform_branch_name(name) for name in names]

def get_artifact_branches(artifactory_host, artifactory_api_key, artifactory_repository):
    url = 'https://{}/artifactory/api/storage/{}/'.format(artifactory_host, artifactory_repository)
    headers = { 'X-JFrog-Art-Api': artifactory_api_key }

    request = Request(url, headers=headers, method='GET')
    response_body = json.load(urlopen(request))

    return [child['uri'][1:] for child in response_body['children'] if child['folder'] == True]

def delete_branch(artifactory_host, artifactory_api_key, artifactory_repository, branch_name):
    url = 'https://{}/artifactory/{}/{}'.format(artifactory_host, artifactory_repository, branch_name)
    headers = { 'X-JFrog-Art-Api': artifactory_api_key }

    request = Request(url, headers=headers, method='DELETE')
    response = urlopen(request)

    if response.status != 204:
        raise RuntimeError('Failed to delete version. Status: {}, reason: {}'.format(response.status, response.reason))
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Delete old Artifactory artifacts')
    parser.add_argument('--artifactory-host', '-H', required = True)
    parser.add_argument('--artifactory-api-key', '-K', required = True)
    parser.add_argument('--artifactory-repository', '-R', required = True)
    parser.add_argument('--current-branch', '-b', required = True)
    parser.add_argument('--github-repository', '-r', required = True)
    parser.add_argument('--github-token', '-t')

    arguments = parser.parse_args()

    existing_branches = get_existing_branches(arguments.github_repository, arguments.github_token)

    existing_branches = transform_branch_names(existing_branches)
    current_branch = transform_branch_name(arguments.current_branch)

    artifact_branches = get_artifact_branches(arguments.artifactory_host, arguments.artifactory_api_key, arguments.artifactory_repository)

    branches_to_delete = [ branch for branch in artifact_branches if branch not in existing_branches or branch == current_branch]

    if len(branches_to_delete) == 0:
        print('No artifact branches will be deleted')

    for branch in branches_to_delete:
        print('Deleting from Artifactory: {}'.format(branch))

        delete_branch(arguments.artifactory_host, arguments.artifactory_api_key, arguments.artifactory_repository, branch)
