import datetime
import json
import os.path
import subprocess

import sys
import yaml

actions = {"then", "else", "then-mode", "else-mode", "then-status", "else-status"}


def write_output(output, status, modes):
    with open(output, "w") as output:
        json.dump({
            "utc": datetime.datetime.utcnow().isoformat(),
            "status": status,
            "modes": modes
        }, output, indent=2)


def execute(command):
    return subprocess.Popen(command, shell=True, stdout=sys.stdout, stderr=sys.stderr).wait() == 0


def read(directory):
    if os.path.isdir(directory):
        for filename in sorted(os.listdir(directory)):
            with open(os.path.join(directory, filename)) as file:
                yield from yaml.load(file, Loader=yaml.BaseLoader)  # uses the yaml baseloader to preserve all strings


def heal(directory, output):
    steps = []
    modes = []

    for step in read(directory):
        if not step.get("if") or len(actions.intersection(step.keys())) != 1:
            print("error: at least one step is missing an 'if' key or hasn't exactly one key amongst " + str(sorted(actions)))
            exit(1)
        if step.get("then-mode"):
            if execute(step.get("if")):
                modes.append(step.get("then-mode"))
        else:
            steps.append(step)

    for step in steps:
        _if = step.get("if")
        _then = step.get("then")
        _else = step.get("else")
        mode = step.get("if-mode")

        if not mode or mode in modes:
            print("test: " + _if)
            if execute(_if):
                if _then:
                    write_output(output, "fixing", modes)
                    print("test failed! fix: " + _then)
                    execute(_then)

                    print("test again: " + _if)
                    if execute(_if):
                        write_output(output, "ko", modes)
                        print("fix failed!")
                        exit(1)
            else:
                if _else:
                    write_output(output, "fixing", modes)
                    print("test failed! fix: " + _else)
                    execute(_else)

                    print("test again: " + _if)
                    if not execute(_if):
                        write_output(output, "ko", modes)
                        print("fix failed!")
                        exit(1)

            write_output(output, "ok", modes)
