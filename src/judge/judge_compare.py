#!/usr/bin/env python3
# coding:utf-8


def do_compare(value1, compare, reference_value):
    if compare == '>':
        if value1 > reference_value:
            judge_result = True
        else:
            judge_result = False
    elif compare == '<':
        if value1 < reference_value:
            judge_result = True
        else:
            judge_result = False
    elif compare == '=':
        if value1 == reference_value:
            judge_result = True
        else:
            judge_result = False
    elif compare == '>=':
        if value1 >= reference_value:
            judge_result = True
        else:
            judge_result = False
    elif compare == '<=':
        if value1 <= reference_value:
            judge_result = True
        else:
            judge_result = False
    elif compare == '!=':
        if value1 != reference_value:
            judge_result = True
        else:
            judge_result = False
    else:
        judge_result = False
    return judge_result


if __name__ == "__main__":
    do_compare('xxx', 'xxx', 'xxx')
