#
# Copyright (C) 2006-2013 Wyplay, All Rights Reserved.
#

import sys, color

verbose_val = False

def verbose(enable):
        global verbose_val
        if enable == True:
                verbose_val = True
        else:
                verbose_val = False

def _print(str, eol=True, output=sys.stdout):
        print >>output, str,
        if eol:
                print >>output
        else:
                sys.stdout.flush()

def die(str=None, output=sys.stdout):
        if str is not None:
                _print(color.red(" * ") + str, False, output)
        sys.exit(1)

def warn(str, eol=True, output=sys.stdout):
        _print(color.yellow(" * ") + str, eol, output)

def error(str, eol=True, output=sys.stdout):
        _print(color.red(" * ") + str, eol, output)

def vinfo(str, eol=True, output=sys.stdout):
        global verbose_val
        if verbose_val:
                _print(color.green(" * ") + str, eol, output)

def info(str, eol=True, output=sys.stdout):
        _print(color.green(" * ") + str, eol, output)

def is_verbose():
        return verbose_val

def userquery(prompt, output=sys.stdout):
        _print(color.bold(prompt), False, output)
        _print('[%s/%s]' % (color.green('Yes'), color.red('No')), False, output)

        while True:
                res = raw_input()
                if not res or res.upper() == "YES":
                        return True
                elif res.upper() == "NO":
                        return False
                else:
                        _print("Sorry, response '%s' not understood." % res, True, output)

