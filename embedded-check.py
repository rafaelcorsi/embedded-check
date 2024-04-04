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
        self.all_vars_with_ass = []
        self.global_vars = []
        self.global_vars_with_ass = []
        self.local_vars = []
        self.isr_global_vars = []
        self.isr_global_vars_id = []
        self.isr_functions = []
        self.isr_functions_names = []

    def update(self):
        local = [i for i in self.all_vars_with_ass if not i in self.global_vars or self.global_vars.remove(i)]
        self.local_vars = local

        self.isr_functions_names = [_.name for _ in self.isr_functions]

        # detecr vars that are used by irs
        isr_global_vars = []
        isr_global_vars_id = []
        for ass in self.all_vars_with_ass:
            if ass["className"] in self.isr_functions_names:
                isr_global_vars.append(ass)
                isr_global_vars_id.append(ass['variable'].Id)
        self.isr_global_vars = isr_global_vars
        self.isr_global_vars_id = isr_global_vars_id

    def iterate_lists(self):
        for attr_name, attr_value in self.__dict__.items():
            if isinstance(attr_value, list):
                for item in attr_value:
                    print(item)

    def append(self, prop_name, other):
        current_prop = getattr(self, prop_name, [])

        if not isinstance(current_prop, list):
            raise ValueError(f"Expected a list for '{prop_name}', got {type(current_prop)} instead.")

        new_prop = current_prop + [i for i in other if i not in current_prop]

        setattr(self, prop_name, new_prop)

    def search_extern_origin(self, extern):
        for v in self.isr_global_vars:
            if v['variable'].nameToken.str == extern['variable'].nameToken.str:
                return v
        return None



class RtosData:
    task_functions = []


class ExtractCodeInfo:
    def __init__(self, dump, code, config):
        self.config = config.config
        self.dump = dump
        self.cfg = self.dump.cfg

        code.append('all_vars_with_ass', self.get_all_vars_with_ass())
        code.append('global_vars', self.get_global_vars())
        code.append('global_vars_with_ass', self.get_global_vars_with_ass())
        code.append('isr_functions', self.get_isr_functions())
        code.update()

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

    def is_funq_isr(self, f):
        res = [ele for ele in self.config["settings"]['isr_names_modifiers'] if (ele in f.name)]
        return True if res else False

    def get_isr_functions(self):
        isr_funcs = []
        # from modifiers name
        for f in self.cfg.functions:
            if self.is_funq_isr(f):
                if f != None:
                    isr_funcs.append(f)

        # from calling a function
        for token in self.cfg.tokenlist:
            if isFunctionCall(token):
                if token.previous.str in self.config['settings']['isr_config_callback']:
                    func_arg = getArguments(token)[-1]
                    if func_arg.str == "&":
                        # using function pointer a.k &btn_callback
                        func = func_arg.next
                    else:
                        # using only btn_callback
                        func = func_arg

                    if func.function is not None:
                        isr_funcs.append(func.function)

        res = []
        [res.append(x) for x in isr_funcs if x not in res]
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
    def __init__ (self, dump_file, ec_code, ec_config):
        self.config = ec_config.config
        self.code = ec_code
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
        Rule 1_2: All global variables assigment in ISR or Callback
        should be volatile
        """

        erro = 0
        var_erro_list_id = []
        for var in self.code.isr_global_vars:
            # excluce specific types exceptions
            var_type = var["variable"].typeStartToken.str
            if [ele for ele in self.config["settings"]['isr_var_types_exceptions'] if (ele in var_type)]:
                continue

            # skip duplicate error
            if var["variable"].Id in var_erro_list_id:
                continue

            if not var["variable"].isVolatile:
                var_name = var["variable"].nameToken.str
                func_name = var["className"]
                self.print_rule_violation(
                    'rule_1_2',
                    f"variable {var_name} in function {func_name}",
                )

                var_erro_list_id.append(var["variable"].Id)
                erro = erro + 1

        return erro

    def rule_1_3(self):
        """
        Rule 1_3: Do not use volatile where is not need
        """

        erro = 0
        var_erro_list_id = []

        for ass in self.code.all_vars_with_ass:
            if ass['variable'].Id in var_erro_list_id:
                continue

            # exclue ISR access vars
            if ass['variable'].Id in self.code.isr_global_vars_id:
                continue

            if ass['variable'].isExtern:
                continue

            if ass["variable"].isVolatile:
                var_name = ass["variable"].nameToken.str
                func_name = ass["className"]
                self.print_rule_violation(
                    'rule_1_3',
                    f"variable {var_name} in function {func_name}",
                )
                var_erro_list_id.append(ass['variable'].Id)
                erro = erro + 1
        return erro

    def rule_1_4(self):
        """
        Rule 1_4: only use global vars for IRS
        """

        erro = 0

        # interact in global avars only assigments
        var_erro_list_id = []
        for ass in self.code.global_vars_with_ass:
            # excluce specific types exceptions (, lcd)
            if ass["variable"].typeStartToken.str in self.config["rule_1_4"]['exceptions']:
                continue

            # exclude var that are accessed in Isr
            if ass["variable"].Id in self.code.isr_global_vars_id:
                continue

            # skip duplicate error
            if ass["variable"].Id in var_erro_list_id:
                continue

            # allow constant global var!
            if ass['variable'].constness:
                continue

            if ass['variable'].isExtern:
                v = self.code.search_extern_origin(ass)
                if v is not None:
                    if v['variable'].Id in var_erro_list_id:
                        continue

                    if v['variable'].Id in self.code.isr_global_vars_id:
                        continue

            # erro print
            var_name = ass["variable"].nameToken.str
            file_name = ass['file_name'].removesuffix('.dump')
            self.print_rule_violation (
                "rule_1_4",
                f"{file_name}: global variable {var_name}",
            )
            var_erro_list_id.append(ass["variable"].Id)
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
        help=" specific config",
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
        ExtractCodeInfo(dump, ec_code, ec_config)

        if rtos:
            ExtractRtosInfo(dump, ec_config, ec_rtos)

    ec = embeddedCheck(args.check_path, ec_code, ec_config)

    ec.rule_1_2()
    ec.rule_1_3()
    ec.rule_1_4()

    sys.exit(ec.erro_total)

if __name__ == "__main__":
    main()
