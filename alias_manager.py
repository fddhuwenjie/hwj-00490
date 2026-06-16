import os
import sys


class AliasManager:
    def __init__(self, shell):
        self.shell = shell
        self.aliases = {}
        self.max_expand_depth = 10

    def define(self, name, value):
        self.aliases[name] = value
        return 0

    def remove(self, name):
        if name in self.aliases:
            del self.aliases[name]
            return 0
        print(f"minibash: unalias: {name}: not found", file=sys.stderr)
        return 1

    def list_all(self):
        lines = []
        for name in sorted(self.aliases.keys()):
            lines.append(f"alias {name}='{self.aliases[name]}'")
        return '\n'.join(lines)

    def lookup(self, name):
        return self.aliases.get(name)

    def expand_command(self, command):
        if command not in self.aliases:
            return command
        expanded = self.aliases[command]
        depth = 1
        while depth < self.max_expand_depth:
            words = expanded.split(None, 1)
            if not words:
                break
            first_word = words[0]
            if first_word == command:
                break
            if first_word in self.aliases:
                rest = words[1] if len(words) > 1 else ''
                expanded = self.aliases[first_word]
                if rest:
                    expanded = expanded + ' ' + rest
                depth += 1
            else:
                break
        return expanded

    def has_alias(self, name):
        return name in self.aliases

    def load_rc_file(self, filepath):
        expanded = os.path.expanduser(filepath)
        if not os.path.isfile(expanded):
            return False
        try:
            with open(expanded, 'r') as f:
                lines = f.readlines()
            self.shell.execute_lines(lines)
            return True
        except Exception as e:
            print(f"minibash: {filepath}: {e}", file=sys.stderr)
            return False


class TypeCommand:
    def __init__(self, shell):
        self.shell = shell

    def get_type(self, name):
        if name in ('cd', 'pwd', 'echo', 'exit', 'export', 'unset', 'history',
                     'set', 'source', 'read', 'true', 'false', ':',
                     'jobs', 'fg', 'bg', 'wait', 'alias', 'unalias',
                     'type', 'trap'):
            return 'builtin', name
        if hasattr(self.shell, 'alias_manager') and self.shell.alias_manager.has_alias(name):
            value = self.shell.alias_manager.lookup(name)
            return 'alias', f"alias {name}='{value}'"
        if name in self.shell.functions:
            return 'function', name
        cmd_path = self.shell.find_command(name)
        if cmd_path is not None:
            return 'external', cmd_path
        return None, f"minibash: type: {name}: not found"
