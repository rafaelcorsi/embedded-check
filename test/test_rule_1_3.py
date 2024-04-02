#!/usr/bin/env python3

import pytest
from util import *

def test_rule_1_3_wrong():
    test_name = "rule_1_3_volatile_wrong"
    run_cppcheck(f"{test_name}.c")

    stdout, stderr, return_code = run_check2(f"{test_name}.c.dump")

    expected_outputs = [
        "[wrongUseOfVolatile] variable foo in function main",
        "[wrongUseOfVolatile] variable bar in function main"
    ]

    for expected_output in expected_outputs:
        assert expected_output in stdout, f"Expected output not found: {expected_output}"


def test_rule_1_3_correct():
    test_name = "rule_1_3_volatile_correct"
    run_cppcheck(f"{test_name}.c")

    stdout, stderr, return_code = run_check2(f"{test_name}.c.dump")
    assert return_code == 0, f"Expected return code 0, but got {return_code}"
