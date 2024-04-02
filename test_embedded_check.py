#!/usr/bin/env python3
import subprocess
import pytest

def run_command(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    return result.stdout.decode('utf-8'), result.stderr.decode('utf-8'), result.returncode

def run_cppcheck(file_path):
    cppcheck_command = f"cppcheck --dump {file_path}"
    run_command(cppcheck_command)

def run_check2(dump_file):
    check2_command = f"python embedded-check.py {dump_file}"
    return run_command(check2_command)

def test_rule_1_2_wrong():
    test_name = "test/rule_1_2_volatile_wrong"
    run_cppcheck(f"{test_name}.c")

    stdout, stderr, return_code = run_check2(f"{test_name}.c.dump")

    expected_outputs = [
        "[notVolatileVarIRS] variable pressed in function btn",
        "[notVolatileVarIRS] variable unpressed in function btn"
    ]

    for expected_output in expected_outputs:
        assert expected_output in stdout, f"Expected output not found: {expected_output}"

def test_rule_1_2_correct():
    test_name = "test/rule_1_2_volatile_correct"
    run_cppcheck(f"{test_name}.c")

    stdout, stderr, return_code = run_check2(f"{test_name}.c.dump")
    assert return_code == 0, f"Expected return code 0, but got {return_code}"

def test_rule_1_3_wrong():
    test_name = "test/rule_1_3_volatile_wrong"
    run_cppcheck(f"{test_name}.c")

    stdout, stderr, return_code = run_check2(f"{test_name}.c.dump")

    expected_outputs = [
        "[wrongUseOfVolatile] variable foo in function main",
        "[wrongUseOfVolatile] variable bar in function main"
    ]

    for expected_output in expected_outputs:
        assert expected_output in stdout, f"Expected output not found: {expected_output}"


def test_rule_1_3_correct():
    test_name = "test/rule_1_3_volatile_correct"
    run_cppcheck(f"{test_name}.c")

    stdout, stderr, return_code = run_check2(f"{test_name}.c.dump")
    assert return_code == 0, f"Expected return code 0, but got {return_code}"
