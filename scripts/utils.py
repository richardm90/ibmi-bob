#! /usr/bin/env python3

# Licensed Materials - Property of IBM
# 57XX-XXX
# (c) Copyright IBM Corp. 2021

from ast import List
from enum import Enum
import json
import os
import subprocess
import sys

from scripts.const import FILE_MAX_EXT_LENGTH, FILE_TARGET_MAPPING

class Colors(str, Enum):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def colored(message: str, color: Colors) -> str:
    """Returns a colored message if supported
    """
    return f"{color}{message}{Colors.ENDC}"


def read_ibmi_json(path, parent_value):
    if path.exists():
        with path.open() as f:
            data = json.load(f)
            try:
                objlib = parse_placeholder(data['build']['objlib'])
                
            except Exception:
                objlib = parent_value[0]
            try:
                tgtCcsid = data['build']['tgtCcsid']
            except Exception:
                tgtCcsid = parent_value[1]
            return (objlib, tgtCcsid)
    else:
        return parent_value

def parse_placeholder(varName):
    if varName.startswith("&") and len(varName) > 1:
        varName = varName[1:]
        try:
            value = os.environ[varName]
            return value
        except Exception:
            print(colored(f"{varName} must be defined first in the environment variable.", Colors.FAIL))
            exit(1)
    else:
        return varName

def read_iproj_json(iproj_json_path):
    with iproj_json_path.open() as f:
        iproj_json = json.load(f)
        objlib = parse_placeholder(iproj_json["objlib"]) if "objlib" in iproj_json else ""
        curlib = parse_placeholder(iproj_json["curlib"]) if "curlib" in iproj_json else ""
        if objlib == "*CURLIB":
            if curlib == "*CRTDFT":
                objlib="QGPL"
            else:
                objlib=curlib
        iproj_json["preUsrlibl"] =" ".join(map(lambda lib: parse_placeholder(lib), iproj_json["preUsrlibl"]))
        iproj_json["postUsrlibl"] =" ".join(map(lambda lib: parse_placeholder(lib), iproj_json["postUsrlibl"]))
        iproj_json["includePath"] =" ".join(iproj_json["includePath"])
        iproj_json["objlib"] = objlib
        iproj_json["curlib"] = curlib
        iproj_json["tgtCcsid"] = iproj_json["tgtCcsid"] if "tgtCcsid" in iproj_json else "*JOB"
        return iproj_json

def objlib_to_path(objlib):
    """Returns the path for the given objlib in IFS

    >>> objlib_to_path("TONGKUN")
    '/QSYS.LIB/TONGKUN.LIB'
    """
    if not objlib: raise ValueError()
    return f"/QSYS.LIB/{objlib}.LIB"

def run_command(cmd: List(str)):
    print(colored(f"> {' '.join(cmd)}", Colors.OKGREEN))
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        for c in iter(lambda: process.stdout.read(1), b''): 
            sys.stdout.buffer.write(c)
            sys.stdout.flush()
    except FileNotFoundError as e:
        print(colored(f'Cannot find command {e.filename}!', Colors.FAIL))

def get_compile_target_from_filename(filename: str):
    """ Returns the possible target name for the given filename

    >>> get_compile_target_from_filename("test.PGM.RPGLE")
    'test.PGM'
    >>> get_compile_target_from_filename("test.RPGLE")
    'test.MODULE'
    >>> get_compile_target_from_filename("functionsVAT/VAT300.RPGLE")
    'VAT300.MODULE'
    """
    parts = os.path.basename(filename).split(".")

    ext_len = FILE_MAX_EXT_LENGTH
    while ext_len > 0:
        base, ext = '.'.join(parts[:-ext_len]), '.'.join(parts[-ext_len:]).upper()
        if ext in FILE_TARGET_MAPPING.keys():
            return f'{base}.{FILE_TARGET_MAPPING[ext]}'
        ext_len -= 1

if __name__ == "__main__":
    import doctest
    doctest.testmod()
