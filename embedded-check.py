#!/usr/bin/env python3
import argparse
import csv
import os
import sys
import yaml
from glob import glob
import re

from sty import bg, ef, fg, rs
from tabulate import tabulate

sys.path.insert(0, './cppcheck')
import cppcheckdata
from misra import getArguments, isFunctionCall


def is_header(file):
    return file.lower().endswith(".h")


def get_dump_files(check_path):
    if os.path.isdir(check_path):
        files = [y for x in os.walk(check_path) for y in glob(os.path.join(x[0], "*.dump"))]
    else:
        files = [check_path]
    return files


class Config:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = self.read_config()

    def read_config(self):
        #rules_yml = rules_yml_default if self.config_file is None else self.config_file
        with open(self.config_file, "r") as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
                return None


class Dump:
    def __init__(self, dump_file):
        self.dump_file = dump_file
        self.file_name = os.path.basename(dump_file)
        self.cfg = self.get_cfg()

    def get_vars(self):
        return self.cfg.variables

    def get_scopes(self):
        return self.cfg.scopes

    def get_scope(self, token):
        scope = token.scope
        while scope.type != "Function":
            scope = self.get_previous_scope(scope.Id)
        return scope

    def get_previous_scope(self, scope_id):
        cnt = 0
        scopes = self.get_scopes()
        for scope in scopes:
            if scope.Id == scope_id:
                return scopes[cnt - 1]
            cnt = cnt + 1

    def get_var_ass(self, token):
        var = None
        if token.astOperand1.str == "[":
            t = token.astOperand1

            while t.variable is None:
                t = t.astOperand1
                if t is None:
                    return None
            var = t.variable
        else:
            var = token.astOperand1.variable
        return var

    def get_cfg(self):
        data = cppcheckdata.CppcheckData(self.dump_file)
        cfg = None
        for cfg in data.iterconfigurations():
            if cfg.name != "":
                continue
        return cfg


class CodeData:
    def __init__(self):
        all_vars_with_ass = []
        global_vars = []
        global_vars_with_ass = []
        irs_functions = []
        irs_functions_names = []

    def iterate_lists(self):
        for attr_name, attr_value in self.__dict__.items():
            if isinstance(attr_value, list):
                for item in attr_value:
                    print(item)

    def append(self, other):
        for attr_name, other_list in other.__dict__.items():
            if isinstance(other_list, list) and hasattr(self, attr_name):
                self_list = getattr(self, attr_name)
                if isinstance(self_list, list):
                    self_list.extend(other_list)


class RtosData:
    task_functions = []


class ExtractCodeInfo:
    def __init__(self, dump, config):
        self.config = config.config
        self.dump = dump
        self.cfg = self.dump.cfg
        self.code = CodeData

        self.code.all_vars_with_ass = self.get_all_vars_with_ass()
        self.code.global_vars = self.get_global_vars()
        self.code.global_vars_with_ass = self.get_global_vars_with_ass()
        self.code.irs_functions = self.get_irs_functions()
        self.code.irs_functions_names =  [func.name for func in self.code.irs_functions]

    def get_all_vars_with_ass(self):
        ass = []

        for token in self.cfg.tokenlist:
            if token.isAssignmentOp:
                variable = self.dump.get_var_ass(token)
                if variable is None:
                    continue

                scope = self.dump.get_scope(token)
                ass.append(
                    {
                        "className": scope.className,
                        "variable": variable,
                        "line": token.linenr,
                        "file_name": self.dump.file_name
                    }
                )
        return ass

    def get_global_vars_with_ass(self):
        all_var_ass = self.get_all_vars_with_ass()
        global_vars = self.get_global_vars()

        # create list of global var assigments
        global_ass = []
        for var in global_vars:
            for ass in all_var_ass:
                if var.Id == ass["variable"].Id:
                    global_ass.append(ass)
        return global_ass

    def get_global_vars(self):
        vars = []
        for var in self.cfg.variables:
            if var.isGlobal:
                vars.append(var)
        return vars

    def is_funq_irs(self, f):
        res = [ele for ele in self.config["settings"]['irs_names_modifiers'] if (ele in f.name)]
        return True if res else False

    def get_irs_functions(self):
        irs_funcs = []
        # from modifiers name
        for f in self.cfg.functions:
            if self.is_funq_irs(f):
                if f != None:
                    irs_funcs.append(f)

        # from calling a function
        for token in self.cfg.tokenlist:
            if isFunctionCall(token):
                if token.previous.str in self.config['settings']['irs_config_callback']:
                    func_arg = getArguments(token)[-1]
                    if func_arg.str == "&":
                        # using function pointer a.k &btn_callback
                        func = func_arg.next
                    else:
                        # using only btn_callback
                        func = func_arg

                    if func.function is not None:
                        irs_funcs.append(func.function)

        res = []
        [res.append(x) for x in irs_funcs if x not in res]
        return res


class ExtractRtosInfo:
    def __init__(self, dump, config, ec_rtos):
        self.config = config.config
        self.dump = dump
        self.cfg = self.dump.cfg

        ec_rtos.task_functions = self.get_task_functions()

    def get_task_functions(self):
        # TODO improve to get info from task_create
        task_funcs = []
        for func in self.cfg.functions:
            if func.name.find("task") >= 0:
                task_funcs.append(func)

        return task_funcs


class embeddedCheck:
    def __init__ (self, dump_file, ec_config, ec_code, ec_rtos, rtos ):
        self.config = ec_config.config
        self.code = ec_code
        self.rtos = ec_rtos
        self.erro_log = []
        self.erro_total = 0
        self.files = get_dump_files(dump_file)

    def print_rule_violation(self, rule_number, where):
        self.erro_total = self.erro_total + 1
        id = self.config[rule_number]['id']
        msg = self.config[rule_number]['msg']
        self.erro_log.append(
            {
                "rule": rule_number,
                "id": id,
                "file": where,
                "text": msg,
            }
        )
        print(f" - [{id}] {where} \r\n\t {msg}")

    def rule_1_2(self):
        """
        Rule 1_2: All global variables assigment in IRS or Callback
        should be volatile
        """

        erro = 0
        var_erro_list_id = []
        for ass in self.code.global_vars_with_ass:
            # excluce specific types exceptions (rtos)
            var_type = ass["variable"].typeStartToken.str
            if [ele for ele in self.config["settings"]['irs_var_types_exceptions'] if (ele in var_type)]:
                continue

            # only check for var ass in IRS functions
            if ass["className"] not in self.code.irs_functions_names:
                continue

            # skip duplicate error
            if ass["variable"].Id in var_erro_list_id:
                continue

            if not ass["variable"].isVolatile:
                var_name = ass["variable"].nameToken.str
                func_name = ass["className"]
                self.print_rule_violation(
                    'rule_1_2',
                    f"variable {var_name} in function {func_name}",
                )
                var_erro_list_id.append(ass["variable"].Id)
                erro = erro + 1
        return erro

    def rule_1_3(self):
        """
        Rule 1_3: Do not use volatile where is not need
        """

        erro = 0
        exclude_ass = []
        for ass in self.code.all_vars_with_ass:
            if ass["className"] in self.code.irs_functions_names:
                exclude_ass.append(ass['variable'].nameTokenId)

        for ass in self.code.all_vars_with_ass:
            # exclue IRS access vars
            if ass['variable'].nameTokenId in exclude_ass:
                continue

            if ass["variable"].isVolatile:
                var_name = ass["variable"].nameToken.str
                func_name = ass["className"]
                self.print_rule_violation(
                    'rule_1_3',
                    f"variable {var_name} in function {func_name}",
                )
                erro = erro + 1
        return erro


def main():
    parser = argparse.ArgumentParser(description="Process some dump c file")
    parser.add_argument(
        "check_path", help="check path with dump file created by cppcheck"
    )
    parser.add_argument(
        "--output-file",
        type=argparse.FileType("w"),
        help="csv file name to save result",
    )
    parser.add_argument(
        "--rtos",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="rtos specific config",
    )
    parser.add_argument(
        "--xml",
        action=argparse.BooleanOptionalAction,
        help="print xml",
    )

    args = parser.parse_args()
    rtos = args.rtos
    erro_total = 0
    erro_log = []
    config_file = os.path.join(os.path.dirname(__file__), "config.yml")
    ec_config = Config(config_file)
    ec_code = CodeData()
    ec_rtos = RtosData()

    dump_files = get_dump_files(args.check_path)
    for file in dump_files:
        dump = Dump(file)
        code = ExtractCodeInfo(dump, ec_config)
        ec_code.append(code)

        if rtos:
            ExtractRtosInfo(dump, ec_config, ec_rtos)

    ec = embeddedCheck(args.check_path, ec_config, ec_code, ec_rtos, rtos)
    ec.rule_1_2()
    ec.rule_1_3()

    sys.exit(ec.erro_total)

if __name__ == "__main__":
    main()
