#! /usr/bin/env python


import argparse
import os
import subprocess
from datetime import datetime
import shutil
import sys

cDescription = ""

cDotfileDir = '.dotfiles'
gStowDir = os.path.join(os.environ.get('HOME'), cDotfileDir)
gTargetDir = os.environ.get('HOME')

cConflictsSubdir = "conflicts"

cNow = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
cStowFile = "stow"

cDefaultProfile = "default"

gDry = False

def get_default_profile_dir():
    default_profile = os.path.join(gStowDir, cDefaultProfile)
    if os.path.isdir(default_profile):
        return default_profile
    return gStowDir

def get_profile_dir(profile=None):
    if not profile:
        return get_default_profile_dir()

    profile_dir = os.path.join(gStowDir, profile)

    if not os.path.isdir(profile_dir):
        print("Error: Did not find profile in stow dir: ", profile_dir)
        exit(1)

    return profile_dir

def get_pkg_dir(pkg, profile=None):
    pkg_dir = os.path.join(get_profile_dir(profile), pkg)
    return pkg_dir

def get_stow_file(pkg, profile=None):
    file = os.path.join(get_profile_dir(), pkg + ".stow.conf")
    return file

def create_stow_file(pkg, profile=None):
    return
    file = get_stow_file(pkg)
    try:
        with open(file, 'x') as f:
           f.write("") 
    except FileExistsError:
        pass

def confirm(question="", default_no=True, force_yes=False):
    if force_yes:
        return True
    choices = ' [y/N]: ' if default_no else ' [Y/n]: '
    default_answer = 'n' if default_no else 'y'
    reply = str(input(question + choices)).lower().strip() or default_answer
    if reply[0] == 'y':
        return True
    if reply[0] == 'n':
        return False
    else:
        return False if default_no else True

def create_common_parser():
    parser = argparse.ArgumentParser(description=cDescription)
    parser.add_argument('cmd', type=str, choices=gCommands.keys())
    parser.add_argument('--dry', dest='dry', action='store_true', default=gDry)
    parser.add_argument('--profile', dest='profile', type=str, required=False)
    return parser

def add_to_pkg(pkg, files, profile=None):
    pkg_dir = get_pkg_dir(pkg, profile)

    for file in files:

        if os.path.islink(file):
            print("Is symlink: ", file)
            continue
        relpath = os.path.relpath(file, gTargetDir)
        source = os.path.join(gTargetDir, relpath)
        stow = os.path.join(pkg_dir, relpath)

        print("Adding to pkg [", pkg, "]: ", file)

        if not gDry:
            os.makedirs(pkg_dir, exist_ok=True)
            #create_stow_file(pkg, profile)
            os.makedirs(os.path.dirname(stow), exist_ok=True)
            shutil.move(source, stow)
        else:
            print("mv ", source, stow)

def cmd_add_to_pkg(gargs):
    parser = create_common_parser()
    parser.add_argument('pkg', type=str)
    parser.add_argument('files', nargs='+')

    args = parser.parse_args()

    add_to_pkg(parser.pkg, parser.files, profile=getattr(args, "profile", None))


def get_conflict_files(pkg, profile=None):

    cmd = ['stow', '-t', gTargetDir, '-d', get_profile_dir(profile), '-nv', pkg]

    ps = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    ps2 = subprocess.Popen(['grep', 'existing'], stdin=ps.stderr, stdout=subprocess.PIPE)
    ps3 = subprocess.Popen(['cut', '-d:', '-f2'], stdin=ps2.stdout, stdout=subprocess.PIPE)

    ps.stdout.close()
    ps.stderr.close()
    ps.wait()
    ps2.stdout.close()
    ps2.wait()
    out, err = ps3.communicate()

    files = out.decode().splitlines()
    conflicts = [i.strip() for i in files]
    return conflicts


def cmd_list_conflicts(gargs):
    parser = create_common_parser()
    parser.add_argument('pkg', type=str)

    args = parser.parse_args()

    files = get_conflict_files(args.pkg, profile=getattr(args, "profile", None))
    print(files)

def backup_conflicts(pkg, conflicts, profile=None):
    
    backup_dir = os.path.join(get_profile_dir(profile), cConflictsSubdir, pkg, cNow)

    if len(conflicts) == 0:
        print("No conflicts")
    else:
        print("Conflicts:")

    for file in conflicts:
        source = os.path.join(gTargetDir, file)
        backup = os.path.join(backup_dir, file)

        print("mv", source, backup)

        if not gDry:
            os.makedirs(os.path.dirname(backup), exist_ok=True)
            shutil.move(source, backup)



def stow_pkg(pkg, profile=None):
    conflicts = get_conflict_files(pkg, profile)
    backup_conflicts(pkg, conflicts, profile)

    cmd = ['stow', '-t', gTargetDir, '-d', get_profile_dir(profile), pkg]
    cmd_dry = cmd.copy()
    cmd_dry.append('-n')
    cmd_dry.append('--verbose=2')

    print("<------>")
    ps1 = subprocess.run(cmd_dry, stdout=sys.stdout, stderr=sys.stderr)
    print("<------>")



    if not gDry:
        if not confirm("Stow files?"):
            return
        ps = subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr)



def stow_pkgs(pkgs, profile=None):

    for pkg in pkgs:
        stow_pkg(pkg, profile=profile)

def cmd_stow_pkgs(args):
    parser = create_common_parser()
    parser.add_argument('pkgs', nargs='+')

    args = parser.parse_args()

    stow_pkgs(args.pkgs, profile=getattr(args, "profile", None))

def unstow_pkg(pkg, profile=None):

    profile_dir = get_profile_dir(profile)

    cmd = ['stow', '--delete', '-t', gTargetDir, '-d', profile_dir, pkg]
    cmd_dry = cmd.copy()
    cmd_dry.append('-nv')

    print("<------>")
    ps1 = subprocess.run(cmd_dry, stdout=sys.stdout, stderr=sys.stderr)
    print("<------>")

    if not gDry:
        if not confirm("Unstow files?"):
            return
        ps = subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr)

def unstow_pkgs(pkgs, profile=None):

    for pkg in pkgs:
        unstow_pkg(pkg, profile)

def cmd_unstow(gargs):
    parser = create_common_parser()
    parser.add_argument('pkgs', nargs='+')

    args = parser.parse_args()

    unstow_pkgs(args.pkgs, profile=getattr(args, "profile", None))

gCommands = {
        "add": cmd_add_to_pkg,
        "list-conflicts": cmd_list_conflicts,
        "stow": cmd_stow_pkgs,
        "unstow": cmd_unstow
        }



def parse_args():
    parser = create_common_parser()
    global gDry
    parser.add_argument('positionals', nargs='*')
    

    args = parser.parse_args()
    gDry = args.dry

    return args


def exe_cmd(args):
    if callable(gCommands.get(args.cmd)):
        gCommands.get(args.cmd)(args)
    else:
        print("Command not implemented")

def main():

    args = parse_args()
    exe_cmd(args)


if __name__ == '__main__':
    main()
