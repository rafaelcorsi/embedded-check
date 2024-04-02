#!/usr/bin/env python3
import subprocess

def run_command(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    return result.stdout.decode('utf-8'), result.stderr.decode('utf-8'), result.returncode

def run_cppcheck(file_path):
    cppcheck_command = f"cppcheck --dump {file_path}"
    run_command(cppcheck_command)

def run_check2(dump_file):
    check2_command = f"python embedded-check.py test/{dump_file}"
    return run_command(check2_command)
