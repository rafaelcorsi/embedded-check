#!/usr/bin/env python3

import pytest
from util import *


def test_rule_1_4_wrong_single_file():
    test_name = "rule_1_4_single_file_wrong"
    run_cppcheck(f"{test_name}.c")

    stdout, stderr, return_code = run_check2(f"{test_name}.c.dump")

    expected_outputs = [
        "[wrongUseOfGlobalVar] rule_1_4_single_file_wrong.c: global variable foo"
    ]

    for expected_output in expected_outputs:
        assert expected_output in stdout, f"Expected output not found: {expected_output}"

def test_rule_1_4_wrong_multiple_files():
    test_name = "rule_1_4_multiple_files/"
    run_cppcheck(test_name)

    stdout, stderr, return_code = run_check2(f"{test_name}")

    expected_outputs = [
        "[wrongUseOfGlobalVar] main.c: global variable buzzer",
        "[wrongUseOfGlobalVar] main.c: global variable rodada",
        "[wrongUseOfGlobalVar] arq.c: global variable sequencia",
        "[wrongUseOfGlobalVar] arq.c: global variable game_over",
        "[wrongUseOfGlobalVar] main.c: global variable game_over"
    ]

    for expected_output in expected_outputs:
        assert expected_output in stdout, f"Expected output not found: {expected_output}"



def test_rule_1_4_correct():
    test_name = "rule_1_3_volatile_correct"
    run_cppcheck(f"{test_name}.c")

    stdout, stderr, return_code = run_check2(f"{test_name}.c.dump")
    assert return_code == 0, f"Expected return code 0, but got {return_code}"
