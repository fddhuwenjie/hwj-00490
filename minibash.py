#!/usr/bin/env python3
import os
import sys
import subprocess
import glob
import re
import readline


class Shell:
    def __init__(self):
        self.variables = {}
        self.env = dict(os.environ)
        self.functions = {}
        self.history = []
        self.history_index = 0
        self.last_exit_code = 0
        self.set_e = False
        self.set_x = False
        self.running = True
        self.positional_params = []
        self._completions = []
        self._init_history_file()

    def _init_history_file(self):
        self.history_file = os.path.expanduser("~/.minibash_history")
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r") as f:
                    for line in f:
                        line = line.rstrip("\n")
                        if line:
                            self.history.append(line)
                self.history_index = len(self.history)
            except Exception:
                pass

    def save_history(self):
        try:
            with open(self.history_file, "w") as f:
                for entry in self.history[-500:]:
                    f.write(entry + "\n")
        except Exception:
            pass

    def add_history(self, line):
        if line.strip():
            self.history.append(line)
            self.history_index = len(self.history)

    def get_var(self, name):
        if name in self.variables:
            return self.variables[name]
        if name in self.env:
            return self.env[name]
        return ""

    def set_var(self, name, value):
        self.variables[name] = value
        if name in self.env:
            self.env[name] = value
            os.environ[name] = value

    def export_var(self, name, value=None):
        if value is not None:
            self.variables[name] = value
            self.env[name] = value
            os.environ[name] = value
        elif name in self.variables:
            self.env[name] = self.variables[name]
            os.environ[name] = self.variables[name]

    def unset_var(self, name):
        self.variables.pop(name, None)
        self.env.pop(name, None)
        os.environ.pop(name, None)

    def expand_string(self, text):
        result = []
        i = 0
        while i < len(text):
            if text[i] == '$':
                expanded, consumed = self._expand_dollar(text, i)
                result.append(expanded)
                i += consumed
            elif text[i] == '\\':
                if i + 1 < len(text):
                    result.append(text[i + 1])
                    i += 2
                else:
                    result.append('\\')
                    i += 1
            else:
                result.append(text[i])
                i += 1
        return ''.join(result)

    def _expand_dollar(self, text, pos):
        if pos + 1 >= len(text):
            return '$', 1
        nc = text[pos + 1]
        if nc == '(':
            return self._expand_cmd_sub(text, pos)
        elif nc == '{':
            return self._expand_braced(text, pos)
        elif nc == '?':
            return str(self.last_exit_code), 2
        elif nc == '#':
            return str(len(self.positional_params)), 2
        elif nc == '@':
            return ' '.join(self.positional_params), 2
        elif nc.isdigit():
            idx = int(nc)
            if idx == 0:
                return "minibash", 2
            elif idx <= len(self.positional_params):
                return self.positional_params[idx - 1], 2
            else:
                return "", 2
        elif nc.isalpha() or nc == '_':
            name = ""
            j = pos + 1
            while j < len(text) and (text[j].isalnum() or text[j] == '_'):
                name += text[j]
                j += 1
            return self.get_var(name), j - pos
        else:
            return '$', 1

    def _expand_cmd_sub(self, text, pos):
        depth = 1
        j = pos + 2
        start = j
        while j < len(text) and depth > 0:
            if text[j] == '(' and j > 0 and text[j - 1] == '$':
                depth += 1
            elif text[j] == ')':
                depth -= 1
            j += 1
        cmd_text = text[start:j - 1]
        try:
            output = subprocess.check_output(
                cmd_text, shell=True, stderr=subprocess.DEVNULL,
                env=self.env, cwd=os.getcwd()
            )
            return output.decode('utf-8', errors='replace').rstrip('\n'), j - pos
        except subprocess.CalledProcessError as e:
            self.last_exit_code = e.returncode
            return "", j - pos
        except Exception:
            return "", j - pos

    def _expand_braced(self, text, pos):
        j = pos + 2
        name = ""
        while j < len(text) and text[j] != '}':
            name += text[j]
            j += 1
        if j < len(text):
            j += 1
        if name:
            return self.get_var(name), j - pos
        return "", j - pos

    def expand_globs(self, args):
        result = []
        for arg in args:
            if any(c in arg for c in ('*', '?', '[')):
                matches = glob.glob(arg)
                if matches:
                    matches.sort()
                    result.extend(matches)
                else:
                    result.append(arg)
            else:
                result.append(arg)
        return result

    def tokenize(self, line):
        tokens = []
        i = 0
        line = line.strip()
        while i < len(line):
            if line[i] in ' \t':
                i += 1
                continue
            if line[i] == '#':
                break
            if line[i] == "'":
                token, i = self._read_sq(line, i)
                tokens.append(('sq', token))
            elif line[i] == '"':
                token, i = self._read_dq(line, i)
                tokens.append(('dq', token))
            elif line[i:i + 2] == '&&':
                tokens.append(('op', '&&'))
                i += 2
            elif line[i:i + 2] == '||':
                tokens.append(('op', '||'))
                i += 2
            elif line[i:i + 2] == '>>':
                tokens.append(('redir', '>>'))
                i += 2
            elif line[i:i + 2] == '&>':
                tokens.append(('redir', '&>'))
                i += 2
            elif line[i] == '2' and i + 1 < len(line) and line[i + 1] == '>':
                tokens.append(('redir', '2>'))
                i += 2
            elif line[i] == '>':
                tokens.append(('redir', '>'))
                i += 1
            elif line[i] == '<':
                tokens.append(('redir', '<'))
                i += 1
            elif line[i] == '|':
                tokens.append(('op', '|'))
                i += 1
            elif line[i] == ';':
                tokens.append(('op', ';'))
                i += 1
            elif line[i] == '(':
                tokens.append(('op', '('))
                i += 1
            elif line[i] == ')':
                tokens.append(('op', ')'))
                i += 1
            elif line[i] == '{':
                tokens.append(('op', '{'))
                i += 1
            elif line[i] == '}':
                tokens.append(('op', '}'))
                i += 1
            else:
                token, i = self._read_word(line, i)
                tokens.append(('word', token))
        return tokens

    def _read_sq(self, line, pos):
        result = []
        i = pos + 1
        while i < len(line) and line[i] != "'":
            result.append(line[i])
            i += 1
        if i < len(line):
            i += 1
        return ''.join(result), i

    def _read_dq(self, line, pos):
        result = []
        i = pos + 1
        while i < len(line) and line[i] != '"':
            if line[i] == '\\' and i + 1 < len(line) and line[i + 1] in ('"', '\\', '$', '`'):
                result.append(line[i + 1])
                i += 2
            else:
                result.append(line[i])
                i += 1
        if i < len(line):
            i += 1
        return ''.join(result), i

    def _read_word(self, line, pos):
        result = []
        i = pos
        while i < len(line):
            c = line[i]
            if c in (' ', '\t', '|', ';', '>', '<', '&', '(', ')', '{', '}', '#'):
                break
            if c in ('"', "'") and result and result[-1] == '=':
                quote_char = c
                result.append(quote_char)
                i += 1
                while i < len(line) and line[i] != quote_char:
                    if quote_char == '"' and line[i] == '\\' and i + 1 < len(line) and line[i + 1] in ('"', '\\', '$', '`'):
                        result.append(line[i])
                        result.append(line[i + 1])
                        i += 2
                    else:
                        result.append(line[i])
                        i += 1
                if i < len(line):
                    result.append(quote_char)
                    i += 1
            elif c == '\\' and i + 1 < len(line):
                result.append(line[i + 1])
                i += 2
            elif c in ('"', "'"):
                break
            else:
                result.append(c)
                i += 1
        return ''.join(result), i

    def resolve_token(self, tok):
        kind, val = tok
        if kind == 'sq':
            return val
        elif kind == 'dq':
            return self.expand_string(val)
        elif kind == 'word':
            return self._expand_word(val)
        return val

    def _expand_word(self, text):
        if '"' not in text and "'" not in text and '$' not in text:
            return text
        result = []
        i = 0
        while i < len(text):
            if text[i] == '"':
                i += 1
                while i < len(text) and text[i] != '"':
                    if text[i] == '\\' and i + 1 < len(text) and text[i + 1] in ('"', '\\', '$', '`'):
                        result.append(text[i + 1])
                        i += 2
                    elif text[i] == '$':
                        expanded, consumed = self._expand_dollar(text, i)
                        result.append(expanded)
                        i += consumed
                    else:
                        result.append(text[i])
                        i += 1
                if i < len(text):
                    i += 1
            elif text[i] == "'":
                i += 1
                while i < len(text) and text[i] != "'":
                    result.append(text[i])
                    i += 1
                if i < len(text):
                    i += 1
            elif text[i] == '$':
                expanded, consumed = self._expand_dollar(text, i)
                result.append(expanded)
                i += consumed
            elif text[i] == '\\' and i + 1 < len(text):
                result.append(text[i + 1])
                i += 2
            else:
                result.append(text[i])
                i += 1
        return ''.join(result)

    def resolve_tokens(self, tokens):
        return [self.resolve_token(t) for t in tokens]

    def find_command(self, cmd):
        if '/' in cmd:
            if os.path.isfile(cmd) and os.access(cmd, os.X_OK):
                return cmd
            return None
        path_dirs = self.env.get('PATH', '').split(':')
        for d in path_dirs:
            full = os.path.join(d, cmd)
            if os.path.isfile(full) and os.access(full, os.X_OK):
                return full
        return None

    def execute_builtin(self, cmd, args, redirs=None):
        if cmd == 'exit':
            code = 0
            if args:
                try:
                    code = int(args[0])
                except ValueError:
                    code = 1
            self.running = False
            self.last_exit_code = code
            return code
        saved_out = None
        saved_err = None
        redir_fds = []
        try:
            if redirs:
                for rtype, rfile in redirs:
                    if rtype == '>':
                        fd = os.open(rfile, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
                        redir_fds.append(fd)
                        if saved_out is None:
                            saved_out = os.dup(1)
                        os.dup2(fd, 1)
                    elif rtype == '>>':
                        fd = os.open(rfile, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
                        redir_fds.append(fd)
                        if saved_out is None:
                            saved_out = os.dup(1)
                        os.dup2(fd, 1)
                    elif rtype == '2>':
                        fd = os.open(rfile, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
                        redir_fds.append(fd)
                        if saved_err is None:
                            saved_err = os.dup(2)
                        os.dup2(fd, 2)
                    elif rtype == '&>':
                        fd = os.open(rfile, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
                        redir_fds.append(fd)
                        if saved_out is None:
                            saved_out = os.dup(1)
                        if saved_err is None:
                            saved_err = os.dup(2)
                        os.dup2(fd, 1)
                        os.dup2(fd, 2)
            sys.stdout.flush()
            sys.stderr.flush()
            result = self._do_builtin(cmd, args)
            sys.stdout.flush()
            sys.stderr.flush()
            return result
        finally:
            if saved_out is not None:
                os.dup2(saved_out, 1)
                os.close(saved_out)
            if saved_err is not None:
                os.dup2(saved_err, 2)
                os.close(saved_err)
            for fd in redir_fds:
                try:
                    os.close(fd)
                except OSError:
                    pass

    def _do_builtin(self, cmd, args):
        if cmd == 'cd':
            target = args[0] if args else self.get_var('HOME')
            if target == '-':
                target = self.get_var('OLDPWD') or self.get_var('HOME')
            try:
                old = os.getcwd()
                os.chdir(target)
                self.set_var('OLDPWD', old)
                self.env['OLDPWD'] = old
                os.environ['OLDPWD'] = old
                new = os.getcwd()
                self.set_var('PWD', new)
                self.env['PWD'] = new
                os.environ['PWD'] = new
                self.last_exit_code = 0
                return 0
            except FileNotFoundError:
                print(f"minibash: cd: {target}: No such file or directory", file=sys.stderr)
                self.last_exit_code = 1
                return 1
            except NotADirectoryError:
                print(f"minibash: cd: {target}: Not a directory", file=sys.stderr)
                self.last_exit_code = 1
                return 1
            except PermissionError:
                print(f"minibash: cd: {target}: Permission denied", file=sys.stderr)
                self.last_exit_code = 1
                return 1
        elif cmd == 'pwd':
            print(os.getcwd())
            self.last_exit_code = 0
            return 0
        elif cmd == 'echo':
            print(' '.join(args))
            self.last_exit_code = 0
            return 0
        elif cmd == 'export':
            for arg in args:
                if '=' in arg:
                    name, _, value = arg.partition('=')
                    self.export_var(name, value)
                else:
                    self.export_var(arg)
            self.last_exit_code = 0
            return 0
        elif cmd == 'unset':
            for arg in args:
                self.unset_var(arg)
            self.last_exit_code = 0
            return 0
        elif cmd == 'history':
            for idx, entry in enumerate(self.history, 1):
                print(f"  {idx:4d}  {entry}")
            self.last_exit_code = 0
            return 0
        elif cmd == 'set':
            for arg in args:
                if arg == '-e':
                    self.set_e = True
                elif arg == '+e':
                    self.set_e = False
                elif arg == '-x':
                    self.set_x = True
                elif arg == '+x':
                    self.set_x = False
            self.last_exit_code = 0
            return 0
        elif cmd == 'source':
            if not args:
                print("minibash: source: filename argument required", file=sys.stderr)
                self.last_exit_code = 1
                return 1
            return self.source_script(args[0])
        elif cmd == 'true':
            self.last_exit_code = 0
            return 0
        elif cmd == 'false':
            self.last_exit_code = 1
            return 1
        elif cmd == ':':
            self.last_exit_code = 0
            return 0
        elif cmd == 'read':
            prompt = ""
            var_names = list(args)
            if var_names and var_names[0].startswith('-p'):
                if len(var_names) > 1:
                    prompt = var_names[1]
                    var_names = var_names[2:]
                else:
                    var_names = var_names[1:]
            if not var_names:
                var_names = ['REPLY']
            try:
                if prompt:
                    sys.stdout.write(prompt)
                    sys.stdout.flush()
                line = input()
                parts = line.split(None, len(var_names) - 1)
                while len(parts) < len(var_names):
                    parts.append('')
                for name, val in zip(var_names, parts):
                    self.set_var(name, val)
                self.last_exit_code = 0
                return 0
            except EOFError:
                self.last_exit_code = 1
                return 1
        return None

    def source_script(self, filename):
        expanded = os.path.expanduser(filename)
        if not os.path.isfile(expanded):
            print(f"minibash: source: {filename}: No such file or directory", file=sys.stderr)
            self.last_exit_code = 1
            return 1
        try:
            with open(expanded, 'r') as f:
                lines = f.readlines()
            return self.execute_lines(lines)
        except Exception as e:
            print(f"minibash: source: {filename}: {e}", file=sys.stderr)
            self.last_exit_code = 1
            return 1

    def execute_lines(self, lines):
        code = 0
        i = 0
        while i < len(lines):
            raw = lines[i].rstrip('\n')
            stripped = raw.strip()
            if not stripped or stripped.startswith('#'):
                i += 1
                continue
            full_line = raw
            while full_line.rstrip().endswith('\\') and i + 1 < len(lines):
                i += 1
                full_line = full_line.rstrip()[:-1] + ' ' + lines[i].rstrip('\n')
            if self._needs_more_lines(full_line):
                while i + 1 < len(lines):
                    i += 1
                    full_line += '\n' + lines[i].rstrip('\n')
                    if not self._needs_more_lines(full_line):
                        break
            code = self.execute_block(full_line)
            if not self.running:
                return code
            if self.set_e and code != 0:
                return code
            i += 1
        return code

    def _needs_more_lines(self, text):
        flat = text.replace('\n', ' ')
        tokens = self.tokenize(flat)
        if not tokens:
            return False
        kinds = [t[0] for t in tokens]
        vals = [t[1] for t in tokens]
        kw_set = {'if', 'while', 'for', 'function'}
        if vals[0] in kw_set:
            if 'fi' not in vals and 'done' not in vals and '}' not in vals:
                return True
        if '(' in vals and ')' not in vals:
            return True
        if '{' in vals and '}' not in vals:
            return True
        if vals[0] == 'do' or vals[0] == 'then':
            return True
        return False

    def execute_block(self, text):
        text = text.strip()
        if not text or text.startswith('#'):
            return 0
        self.add_history(text)
        if self.set_x:
            print(f"+ {text}", file=sys.stderr)
        try:
            return self._dispatch_block(text)
        except Exception as e:
            print(f"minibash: error: {e}", file=sys.stderr)
            self.last_exit_code = 1
            return 1

    def _dispatch_block(self, text):
        flat = text.replace('\n', ' ; ')
        tokens = self.tokenize(flat)
        if not tokens:
            return 0
        first_val = tokens[0][1]
        if first_val == 'if':
            return self._exec_if_from_text(text)
        elif first_val == 'while':
            return self._exec_while_from_text(text)
        elif first_val == 'for':
            return self._exec_for_from_text(text)
        elif first_val == 'function' or self._is_func_def(tokens):
            return self._def_func_from_text(text, tokens)
        else:
            return self._exec_simple_text(text)

    def _is_func_def(self, tokens):
        if len(tokens) >= 3:
            if tokens[0][0] == 'word' and tokens[1][1] == '(' and tokens[2][1] == ')':
                return True
        return False

    def _exec_simple_text(self, text):
        tokens = self.tokenize(text)
        if not tokens:
            return 0
        first = self.resolve_token(tokens[0])
        if '=' in first and not first.startswith('='):
            name, _, value = first.partition('=')
            if name and re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
                expanded_value = self.expand_string(value)
                if len(tokens) == 1:
                    self.set_var(name, expanded_value)
                    self.last_exit_code = 0
                    return 0
        return self._exec_tokens_chain(tokens)

    def _exec_tokens_chain(self, tokens):
        semi_groups = self._split_by_op(tokens, ';')
        result = 0
        for group in semi_groups:
            if not group:
                continue
            result = self._exec_and_or(group)
            if not self.running:
                return result
            if self.set_e and result != 0:
                return result
        return result

    def _split_by_op(self, tokens, op_val):
        groups = []
        current = []
        for t in tokens:
            if t[0] == 'op' and t[1] == op_val:
                if current:
                    groups.append(current)
                    current = []
            else:
                current.append(t)
        if current:
            groups.append(current)
        return groups

    def _exec_and_or(self, tokens):
        segments = []
        current = []
        pending_op = None
        for t in tokens:
            if t[0] == 'op' and t[1] in ('&&', '||'):
                if current:
                    segments.append((pending_op, current))
                    current = []
                pending_op = t[1]
            else:
                current.append(t)
        if current:
            segments.append((pending_op, current))
        if not segments:
            return 0
        result = self._exec_pipeline(segments[0][1])
        for j in range(1, len(segments)):
            op, cmd_tokens = segments[j]
            if op == '&&':
                if result == 0:
                    result = self._exec_pipeline(cmd_tokens)
            elif op == '||':
                if result != 0:
                    result = self._exec_pipeline(cmd_tokens)
        return result

    def _exec_pipeline(self, tokens):
        pipe_groups = self._split_by_op(tokens, '|')
        if not pipe_groups:
            return 0
        if len(pipe_groups) == 1:
            return self._exec_single_cmd(pipe_groups[0])
        return self._exec_pipe_chain(pipe_groups)

    def _exec_pipe_chain(self, groups):
        prev_read = None
        last_code = 0
        for i, group in enumerate(groups):
            redirs = self._extract_redirections(group)
            if i < len(groups) - 1:
                r_fd, w_fd = os.pipe()
            else:
                r_fd, w_fd = None, None
            resolved = self.resolve_tokens(group)
            resolved = self.expand_globs(resolved)
            if not resolved:
                if prev_read is not None:
                    os.close(prev_read)
                if w_fd is not None:
                    os.close(w_fd)
                continue
            cmd = resolved[0]
            args = resolved[1:]
            stdin_fd = prev_read
            stdout_fd = w_fd
            builtin_res = self._try_builtin_with_fds(cmd, args, stdin_fd, stdout_fd, redirs)
            if builtin_res is not None:
                last_code = builtin_res
            elif cmd in self.functions:
                if stdout_fd is not None:
                    old_stdout = os.dup(1)
                    os.dup2(stdout_fd, 1)
                    os.close(stdout_fd)
                if stdin_fd is not None:
                    old_stdin = os.dup(0)
                    os.dup2(stdin_fd, 0)
                    os.close(stdin_fd)
                last_code = self._call_function(cmd, args)
                if stdout_fd is not None:
                    os.dup2(old_stdout, 1)
                    os.close(old_stdout)
                if stdin_fd is not None:
                    os.dup2(old_stdin, 0)
                    os.close(old_stdin)
            else:
                cmd_path = self.find_command(cmd)
                if cmd_path is None:
                    print(f"minibash: {cmd}: command not found", file=sys.stderr)
                    last_code = 127
                else:
                    try:
                        stdin_arg = stdin_fd
                        stdout_arg = stdout_fd
                        stderr_arg = None
                        for rtype, rfile in redirs:
                            if rtype == '<':
                                stdin_arg = os.open(rfile, os.O_RDONLY)
                            elif rtype == '>':
                                stdout_arg = os.open(rfile, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
                            elif rtype == '>>':
                                stdout_arg = os.open(rfile, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
                            elif rtype == '2>':
                                stderr_arg = os.open(rfile, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
                            elif rtype == '&>':
                                fd = os.open(rfile, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
                                stdout_arg = fd
                                stderr_arg = fd
                        proc = subprocess.Popen(
                            [cmd_path] + args,
                            stdin=stdin_arg,
                            stdout=stdout_arg,
                            stderr=stderr_arg,
                            env=self.env,
                            cwd=os.getcwd()
                        )
                        proc.wait()
                        last_code = proc.returncode
                    except Exception as e:
                        print(f"minibash: {cmd}: {e}", file=sys.stderr)
                        last_code = 1
            if prev_read is not None:
                os.close(prev_read)
                prev_read = None
            if r_fd is not None:
                prev_read = r_fd
            if w_fd is not None:
                os.close(w_fd)
        self.last_exit_code = last_code
        return last_code

    def _try_builtin_with_fds(self, cmd, args, stdin_fd, stdout_fd, redirs):
        if cmd not in ('echo', 'pwd', 'cd', 'exit', 'export', 'unset', 'history',
                       'set', 'source', 'read', 'true', 'false', ':'):
            return None
        old_out = None
        old_in = None
        redirect_file = None
        stdin_file = None
        try:
            if stdout_fd is not None:
                old_out = os.dup(1)
                os.dup2(stdout_fd, 1)
            if stdin_fd is not None:
                old_in = os.dup(0)
                os.dup2(stdin_fd, 0)
            for rtype, rfile in redirs:
                if rtype == '>':
                    redirect_file = os.open(rfile, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
                    if old_out is None:
                        old_out = os.dup(1)
                    os.dup2(redirect_file, 1)
                elif rtype == '>>':
                    redirect_file = os.open(rfile, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
                    if old_out is None:
                        old_out = os.dup(1)
                    os.dup2(redirect_file, 1)
                elif rtype == '<':
                    stdin_file = os.open(rfile, os.O_RDONLY)
                    if old_in is None:
                        old_in = os.dup(0)
                    os.dup2(stdin_file, 0)
            return self.execute_builtin(cmd, args, redirs=None)
        finally:
            if redirect_file is not None:
                os.close(redirect_file)
            if stdin_file is not None:
                os.close(stdin_file)
            if old_out is not None:
                os.dup2(old_out, 1)
                os.close(old_out)
            if old_in is not None:
                os.dup2(old_in, 0)
                os.close(old_in)

    def _exec_single_cmd(self, tokens):
        redirs = self._extract_redirections(tokens)
        resolved = self.resolve_tokens(tokens)
        resolved = self.expand_globs(resolved)
        if not resolved:
            return 0
        cmd = resolved[0]
        args = resolved[1:]
        if '=' in cmd and not cmd.startswith('='):
            name, _, value = cmd.partition('=')
            if name and re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
                self.set_var(name, value)
                self.last_exit_code = 0
                return 0
        if cmd in self.functions:
            result = self._call_function(cmd, args)
            self.last_exit_code = result
            return result
        builtin_res = self.execute_builtin(cmd, args, redirs=redirs)
        if builtin_res is not None:
            return builtin_res
        cmd_path = self.find_command(cmd)
        if cmd_path is None:
            print(f"minibash: {cmd}: command not found", file=sys.stderr)
            self.last_exit_code = 127
            return 127
        return self._run_external(cmd_path, args, redirs)

    def _run_external(self, cmd_path, args, redirs):
        stdin_file = None
        stdout_file = None
        stderr_file = None
        combined_file = None
        try:
            for rtype, rfile in redirs:
                if rtype == '<':
                    stdin_file = open(rfile, 'r')
                elif rtype == '>':
                    stdout_file = open(rfile, 'w')
                elif rtype == '>>':
                    stdout_file = open(rfile, 'a')
                elif rtype == '2>':
                    stderr_file = open(rfile, 'w')
                elif rtype == '&>':
                    combined_file = open(rfile, 'w')
            stdin_arg = stdin_file
            stdout_arg = combined_file if combined_file else stdout_file
            stderr_arg = combined_file if combined_file else stderr_file
            proc = subprocess.Popen(
                [cmd_path] + args,
                stdin=stdin_arg,
                stdout=stdout_arg,
                stderr=stderr_arg,
                env=self.env,
                cwd=os.getcwd()
            )
            proc.wait()
            code = proc.returncode
            self.last_exit_code = code
            return code
        except Exception as e:
            print(f"minibash: {cmd_path}: {e}", file=sys.stderr)
            self.last_exit_code = 1
            return 1
        finally:
            for f in [stdin_file, stdout_file, stderr_file, combined_file]:
                if f:
                    f.close()

    def _extract_redirections(self, tokens):
        redirs = []
        new_tokens = []
        i = 0
        while i < len(tokens):
            if tokens[i][0] == 'redir':
                rtype = tokens[i][1]
                if i + 1 < len(tokens):
                    rfile = self.resolve_token(tokens[i + 1])
                    redirs.append((rtype, rfile))
                    i += 2
                else:
                    i += 1
            else:
                new_tokens.append(tokens[i])
                i += 1
        tokens[:] = new_tokens
        return redirs

    def _exec_if_from_text(self, text):
        flat = text.replace('\n', ' ; ')
        tokens = self.tokenize(flat)
        segments = self._parse_if_tokens(tokens)
        if segments is None:
            self.last_exit_code = 2
            return 2
        cond_text, then_body, elif_list, else_body = segments
        cond_code = self._exec_simple_text(cond_text)
        if cond_code == 0:
            return self._exec_body_list(then_body)
        for elif_cond, elif_body in elif_list:
            cond_code = self._exec_simple_text(elif_cond)
            if cond_code == 0:
                return self._exec_body_list(elif_body)
        if else_body:
            return self._exec_body_list(else_body)
        return 0

    def _parse_if_tokens(self, tokens):
        vals = [t[1] for t in tokens]
        try:
            if_pos = vals.index('if')
            then_pos = vals.index('then')
            fi_pos = len(vals) - 1 - vals[::-1].index('fi')
        except ValueError:
            print("minibash: syntax error: incomplete if", file=sys.stderr)
            return None
        cond_text = self._tokens_to_text(tokens[if_pos + 1:then_pos])
        elif_list = []
        else_body = None
        then_end = fi_pos
        elif_positions = [i for i, v in enumerate(vals) if v == 'elif']
        else_position = None
        try:
            else_position = vals.index('else')
        except ValueError:
            pass
        if elif_positions or else_position is not None:
            sections = []
            sections.append(('then', then_pos))
            for ep in elif_positions:
                sections.append(('elif', ep))
            if else_position is not None:
                sections.append(('else', else_position))
            sections.append(('fi', fi_pos))
            for si in range(len(sections) - 1):
                sec_type, sec_pos = sections[si]
                next_type, next_pos = sections[si + 1]
                if sec_type == 'then':
                    body = self._tokens_to_text(tokens[sec_pos + 1:next_pos])
                    then_body = [body]
                elif sec_type == 'elif':
                    then_in_elif = vals.index('then', sec_pos + 1)
                    elif_cond = self._tokens_to_text(tokens[sec_pos + 1:then_in_elif])
                    elif_body_text = self._tokens_to_text(tokens[then_in_elif + 1:next_pos])
                    elif_list.append((elif_cond, [elif_body_text]))
                elif sec_type == 'else':
                    else_body = [self._tokens_to_text(tokens[sec_pos + 1:next_pos])]
        else:
            body = self._tokens_to_text(tokens[then_pos + 1:fi_pos])
            then_body = [body]
        return cond_text, then_body, elif_list, else_body

    def _exec_while_from_text(self, text):
        flat = text.replace('\n', ' ; ')
        tokens = self.tokenize(flat)
        vals = [t[1] for t in tokens]
        try:
            do_pos = vals.index('do')
            done_pos = len(vals) - 1 - vals[::-1].index('done')
        except ValueError:
            print("minibash: syntax error: incomplete while", file=sys.stderr)
            self.last_exit_code = 2
            return 2
        cond_text = self._tokens_to_text(tokens[1:do_pos])
        body_text = self._tokens_to_text(tokens[do_pos + 1:done_pos])
        result = 0
        max_iter = 10000
        for _ in range(max_iter):
            cond_code = self._exec_simple_text(cond_text)
            if cond_code != 0:
                break
            result = self._exec_simple_text(body_text)
            if not self.running:
                return result
            if self.set_e and result != 0:
                return result
        self.last_exit_code = result
        return result

    def _exec_for_from_text(self, text):
        flat = text.replace('\n', ' ; ')
        tokens = self.tokenize(flat)
        vals = [t[1] for t in tokens]
        if len(tokens) < 2:
            print("minibash: syntax error: for needs variable", file=sys.stderr)
            return 2
        var_name = vals[1]
        try:
            in_pos = vals.index('in')
        except ValueError:
            in_pos = None
        try:
            do_pos = vals.index('do')
        except ValueError:
            print("minibash: syntax error: incomplete for", file=sys.stderr)
            return 2
        try:
            done_pos = len(vals) - 1 - vals[::-1].index('done')
        except ValueError:
            print("minibash: syntax error: incomplete for", file=sys.stderr)
            return 2
        if in_pos is not None:
            iter_tokens = tokens[in_pos + 1:do_pos]
            iter_tokens = [t for t in iter_tokens if not (t[0] == 'op')]
            iter_values = self.resolve_tokens(iter_tokens)
            iter_values = self.expand_globs(iter_values)
        else:
            iter_values = []
        body_text = self._tokens_to_text(tokens[do_pos + 1:done_pos])
        result = 0
        for val in iter_values:
            self.set_var(var_name, val)
            result = self._exec_simple_text(body_text)
            if not self.running:
                return result
            if self.set_e and result != 0:
                return result
        self.last_exit_code = result
        return result

    def _def_func_from_text(self, text, tokens):
        vals = [t[1] for t in tokens]
        if vals[0] == 'function':
            name = vals[1]
            if name.endswith('()'):
                name = name[:-2]
        else:
            name = vals[0]
        try:
            open_brace = vals.index('{')
        except ValueError:
            print("minibash: syntax error: function needs { body }", file=sys.stderr)
            return 2
        close_brace = len(vals) - 1 - vals[::-1].index('}')
        body_tokens = tokens[open_brace + 1:close_brace]
        body_text = self._tokens_to_text(body_tokens)
        self.functions[name] = body_text
        self.last_exit_code = 0
        return 0

    def _call_function(self, name, args):
        if name not in self.functions:
            print(f"minibash: {name}: function not found", file=sys.stderr)
            self.last_exit_code = 127
            return 127
        old_params = self.positional_params
        self.positional_params = args
        body_text = self.functions[name]
        result = self._exec_simple_text(body_text)
        self.positional_params = old_params
        self.last_exit_code = result
        return result

    def _tokens_to_text(self, tokens):
        parts = []
        for kind, val in tokens:
            if kind == 'sq':
                parts.append("'" + val + "'")
            elif kind == 'dq':
                parts.append('"' + val + '"')
            elif kind == 'word':
                parts.append(val)
            elif kind == 'op':
                if val in ('&&', '||', '|', ';'):
                    parts.append(' ' + val + ' ')
                else:
                    parts.append(val)
            elif kind == 'redir':
                parts.append(' ' + val + ' ')
            else:
                parts.append(val)
        return ' '.join(' '.join(p.split()) for p in parts).strip()

    def _exec_body_list(self, body_list):
        result = 0
        for body_text in body_list:
            result = self._exec_simple_text(body_text)
            if not self.running:
                return result
            if self.set_e and result != 0:
                return result
        return result

    def setup_readline(self):
        readline.set_completer(self._completer)
        readline.parse_and_bind("tab: complete")
        readline.set_completer_delims(' \t\n;|&<>(){}')
        try:
            readline.read_history_file(self.history_file)
        except FileNotFoundError:
            pass

    def _completer(self, text, state):
        if state == 0:
            line = readline.get_line_buffer()
            if line and not line.startswith(' ') and ' ' not in line:
                path_dirs = self.env.get('PATH', '').split(':')
                self._completions = []
                for d in path_dirs:
                    if os.path.isdir(d):
                        try:
                            for f in os.listdir(d):
                                if f.startswith(text):
                                    full = os.path.join(d, f)
                                    if os.path.isfile(full) and os.access(full, os.X_OK):
                                        self._completions.append(f)
                        except PermissionError:
                            pass
                for fn in self.functions:
                    if fn.startswith(text):
                        self._completions.append(fn)
                builtins = ['cd', 'pwd', 'echo', 'exit', 'export', 'unset', 'history',
                            'set', 'source', 'read', 'true', 'false']
                for b in builtins:
                    if b.startswith(text):
                        self._completions.append(b)
                aliases = list(set(self._completions))
                aliases.sort()
                self._completions = aliases
            else:
                self._completions = glob.glob(text + '*')
                self._completions.sort()
                self._completions = [
                    c + '/' if os.path.isdir(c) else c for c in self._completions
                ]
        if state < len(self._completions):
            return self._completions[state]
        return None

    def run_interactive(self):
        self.setup_readline()
        print("MiniBash - A simplified shell interpreter")
        print("Type 'exit' to quit\n")
        while self.running:
            try:
                cwd = os.getcwd()
                home = self.get_var('HOME')
                if home and cwd.startswith(home):
                    cwd = '~' + cwd[len(home):]
                prompt = f"minibash:{cwd}$ "
                try:
                    line = input(prompt)
                except KeyboardInterrupt:
                    print()
                    continue
                if not line.strip():
                    continue
                if line.strip().startswith('!'):
                    hist_match = line.strip()[1:]
                    if hist_match.isdigit():
                        idx = int(hist_match)
                        if 1 <= idx <= len(self.history):
                            line = self.history[idx - 1]
                            print(line)
                        else:
                            print(f"minibash: !{idx}: event not found", file=sys.stderr)
                            continue
                    else:
                        for entry in reversed(self.history):
                            if entry.startswith(hist_match):
                                line = entry
                                print(line)
                                break
                        else:
                            print(f"minibash: !{hist_match}: event not found", file=sys.stderr)
                            continue
                code = self.execute_block(line)
                self.last_exit_code = code
                try:
                    readline.write_history_file(self.history_file)
                except Exception:
                    pass
            except EOFError:
                print()
                break
        self.save_history()

    def run_script(self, filename):
        expanded = os.path.expanduser(filename)
        if not os.path.isfile(expanded):
            print(f"minibash: {filename}: No such file or directory", file=sys.stderr)
            sys.exit(1)
        try:
            with open(expanded, 'r') as f:
                lines = f.readlines()
            code = self.execute_lines(lines)
            sys.exit(code)
        except Exception as e:
            print(f"minibash: {filename}: {e}", file=sys.stderr)
            sys.exit(1)


def main():
    shell = Shell()
    if len(sys.argv) > 1:
        shell.run_script(sys.argv[1])
    else:
        shell.run_interactive()


if __name__ == '__main__':
    main()
