# /usr/bin/env python


import argparse
import os
import subprocess
from datetime import datetime
import shutil
import sys

gDescription = ""

gDotfileDir = '.dotfiles'
gStowDir = os.path.join(os.environ.get('HOME'), gDotfileDir) 
gTargetDir = os.environ.get('HOME')

gConflictsSubdir = "conflicts"

gNow = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
cStowFile = "stow"

gDry = False

def get_stow_file(pkg):
    file = os.path.join(gStowDir, pkg + ".stow.conf")
    return file

def create_stow_file(pkg):
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
    parser = argparse.ArgumentParser(description=gDescription)
    parser.add_argument('cmd', type=str, choices=gCommands.keys())
    parser.add_argument('--dry', dest='dry', action='store_true', default=gDry)
    return parser

def add_to_pkg(gargs):
    parser = create_common_parser()
    parser.add_argument('pkg', type=str)
    parser.add_argument('files', nargs='+')

    args = parser.parse_args()
    print(args)

    pkg_dir = os.path.join(gStowDir, args.pkg)

    for file in args.files:

        if os.path.islink(file):
            print("Is symlink: ", file)
            continue
        relpath = os.path.relpath(file, gTargetDir)
        source = os.path.join(gTargetDir, relpath)
        stow = os.path.join(pkg_dir, relpath)

        print("Adding to pkg [", args.pkg, "]: ", file)

        if not gDry:
            os.makedirs(pkg_dir, exist_ok=True)
            create_stow_file(args.pkg)
            os.makedirs(os.path.dirname(stow), exist_ok=True)
            shutil.move(source, stow)
        else:
            print("mv ", source, stow)



def get_conflict_files(pkg):

    cmd = ['stow', '-t', gTargetDir, '-d', gStowDir, '-nv', pkg]

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


def list_conflicts(gargs):
    parser = create_common_parser()
    parser.add_argument('pkg', type=str)

    args = parser.parse_args()

    files = get_conflict_files(args.pkg)
    print(files)

def backup_conflicts(pkg, conflicts):
    
    backup_dir = os.path.join(gStowDir, gConflictsSubdir, pkg, gNow)

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



def stow_pkg(pkg):
    conflicts = get_conflict_files(pkg)
    backup_conflicts(pkg, conflicts)

    cmd = ['stow', '-t', gTargetDir, '-d', gStowDir, pkg]
    cmd_dry = cmd.copy()
    cmd_dry.append('-n')
    cmd_dry.append('--verbose=2')

    print("<------>")
    ps1 = subprocess.run(cmd_dry, stdout=sys.stdout, stderr=sys.stderr)
    print("<------>")

    if not confirm("Stow files?"):
        return

    if not gDry:
        ps = subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr)



def stow_pkgs(gargs):
    parser = create_common_parser()
    parser.add_argument('pkgs', nargs='+')

    args = parser.parse_args()

    if len(args.pkgs) == 1 and args.pkgs[0] == "all":
        raise NotImplementedError()



    for pkg in args.pkgs:
        stow_pkg(pkg)



gCommands = {
        "add": add_to_pkg,
        "list-conflicts": list_conflicts,
        "stow": stow_pkgs
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
