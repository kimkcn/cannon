#!/usr/bin/env python3
# coding=utf-8


def func_test():
    import importlib
    #params = importlib.import_module('test.test')  # 绝对导入

    module_path = "test.test"
    clsname = "TestClass"
    function = "test_function"

    #clsname = ""
    #function = "test_2"

    obj = importlib.import_module(module_path)  # import module
    if clsname:
        c = getattr(obj, clsname)
        obj = c()
    mtd = getattr(obj, function)
    mtd()


if __name__ == "__main__":
    func_test()
