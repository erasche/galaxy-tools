#!/usr/bin/env python
import yaml
import sys
import xml.etree.cElementTree as ET

with open(sys.argv[1], 'r') as handle:
    data = yaml.load(handle)

root = ET.Element("tool_dependency")


def handle_dependency(node, dependency, in_build=False):
    if not in_build:
        package = ET.SubElement(node, 'package')
        package.set('name', dependency['name'])
        package.set('version', dependency['vers'])
        repo = ET.SubElement(package, 'repository')
        repo.set('name', dependency['repo_name'])
        repo.set('owner', dependency['repo_owner'])
        if dependency['build_req']:
            repo.set('prior_installation_required', 'True')
    else:
        repo = ET.SubElement(node, 'repository')
        repo.set('name', dependency['repo_name'])
        repo.set('owner', dependency['repo_owner'])
        package = ET.SubElement(repo, 'package')
        package.set('name', dependency['name'])
        package.set('version', dependency['vers'])


def handle_dependencies(node, in_build=False):
    for dependency in data['depends']:
        handle_dependency(node, dependency, in_build)


def handle_download_actions(node):
    if 'git_repo' in data['source']:
        clone = ET.SubElement(node, 'action')
        clone.set('type', 'shell_command')
        clone.text = 'git clone %s %s' % (data['source']['git_repo']['url'], data['meta']['name'])
        set_rev = ET.SubElement(node, 'action')
        set_rev.set('type', 'shell_command')
        set_rev.text = 'git reset --hard %s' % data['source']['git_repo']['rev']
    else:
        raise Exception("Unimplemented source")


def handle_build_commands(node):
    action = ET.SubElement(node, 'action')
    action.set('type', 'shell_command')
    action.text = data['build']['commands'].strip().replace('\n', ' && ')


env_actions = {
    'prepend': 'prepend_to',
    'set': 'set_to',
}


def handle_post_build_env(node):
    action = ET.SubElement(node, 'action')
    action.set('type', 'set_environment')
    for env in data['build']['env']:
        env_var = ET.SubElement(action, 'environment_variable')
        if env['action'] in env_actions:
            env_var.set('action', env_actions[env['action']])
            env_var.set('name', env['name'])
            env_var.text = env['value']


def handle_dependencies_actions(node):
    for dependency in data['depends']:
        if dependency['build_req']:
            action = ET.SubElement(node, 'action')
            action.set('type', 'set_environment_for_install')
            handle_dependency(action, dependency, in_build=True)


def handle_package(node):
    package = ET.SubElement(node, 'package')
    package.set('name', data['meta']['name'])
    package.set('version', data['meta']['vers'])
    install = ET.SubElement(package, 'install')
    install.set('version', '1.0')
    actions = ET.SubElement(install, 'actions')
    handle_download_actions(actions)
    handle_dependencies_actions(actions)
    handle_build_commands(actions)
    handle_post_build_env(actions)

    readme = ET.SubElement(package, 'readme')
    readme.text = data['meta']['readme']

handle_dependencies(root, in_build=False)
handle_package(root)

print ET.tostring(root)
