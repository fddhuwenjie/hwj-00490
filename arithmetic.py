import os
import re


class ArithmeticEvaluator:
    def __init__(self, shell):
        self.shell = shell
        self.pos = 0
        self.text = ""

    def evaluate(self, expression):
        expression = expression.strip()
        if not expression:
            return 0
        self.text = expression
        self.pos = 0
        try:
            result = self._parse_expr()
            self._skip_spaces()
            if self.pos < len(self.text):
                raise ValueError(f"unexpected character: {self.text[self.pos]}")
            return int(result)
        except Exception as e:
            raise ValueError(f"arithmetic evaluation error: {e}")

    def _skip_spaces(self):
        while self.pos < len(self.text) and self.text[self.pos] in ' \t':
            self.pos += 1

    def _peek(self):
        self._skip_spaces()
        if self.pos < len(self.text):
            return self.text[self.pos]
        return None

    def _parse_expr(self):
        return self._parse_or()

    def _parse_or(self):
        left = self._parse_and()
        while self._match('||'):
            right = self._parse_and()
            left = 1 if (left or right) else 0
        return left

    def _parse_and(self):
        left = self._parse_comparison()
        while True:
            if self._match('&&'):
                right = self._parse_comparison()
                left = 1 if (left and right) else 0
            else:
                break
        return left

    def _parse_comparison(self):
        left = self._parse_add()
        while True:
            if self._match('=='):
                right = self._parse_add()
                left = 1 if left == right else 0
            elif self._match('!='):
                right = self._parse_add()
                left = 1 if left != right else 0
            elif self._match('<='):
                right = self._parse_add()
                left = 1 if left <= right else 0
            elif self._match('>='):
                right = self._parse_add()
                left = 1 if left >= right else 0
            elif self._match('<'):
                right = self._parse_add()
                left = 1 if left < right else 0
            elif self._match('>'):
                right = self._parse_add()
                left = 1 if left > right else 0
            else:
                break
        return left

    def _parse_add(self):
        left = self._parse_mul()
        while True:
            if self._match('+'):
                left = left + self._parse_mul()
            elif self._match('-'):
                left = left - self._parse_mul()
            else:
                break
        return left

    def _parse_mul(self):
        left = self._parse_unary()
        while True:
            if self._match('*'):
                left = left * self._parse_unary()
            elif self._match('/'):
                right = self._parse_unary()
                if right == 0:
                    raise ValueError("division by zero")
                left = int(left / right)
            elif self._match('%'):
                right = self._parse_unary()
                if right == 0:
                    raise ValueError("modulo by zero")
                left = left % right
            else:
                break
        return left

    def _parse_unary(self):
        if self._match('!'):
            val = self._parse_unary()
            return 1 if val == 0 else 0
        if self._match('-'):
            return -self._parse_unary()
        if self._match('+'):
            return self._parse_unary()
        if self._match('~'):
            return ~self._parse_unary()
        return self._parse_primary()

    def _parse_primary(self):
        self._skip_spaces()
        if self._match('('):
            val = self._parse_expr()
            if not self._match(')'):
                raise ValueError("missing closing parenthesis")
            return val

        if self.pos < len(self.text) and (self.text[self.pos].isalpha() or self.text[self.pos] == '_'):
            name = self._read_identifier()
            if self._match('='):
                val = self._parse_expr()
                self.shell.set_var(name, str(val))
                return val
            val_str = self.shell.get_var(name)
            if val_str == '':
                return 0
            try:
                return int(val_str)
            except ValueError:
                return 0

        num_str = self._read_number()
        if num_str:
            return int(num_str)

        raise ValueError(f"unexpected character at position {self.pos}: '{self.text[self.pos] if self.pos < len(self.text) else 'EOF'}'")

    def _read_identifier(self):
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
            self.pos += 1
        return self.text[start:self.pos]

    def _read_number(self):
        self._skip_spaces()
        start = self.pos
        if self.pos < len(self.text) and self.text[self.pos] in '0123456789':
            while self.pos < len(self.text) and self.text[self.pos] in '0123456789':
                self.pos += 1
            return self.text[start:self.pos]
        return None

    def _match(self, s):
        self._skip_spaces()
        if self.text[self.pos:self.pos + len(s)] == s:
            self.pos += len(s)
            return True
        return False


class TestEvaluator:
    def __init__(self, shell):
        self.shell = shell

    def evaluate(self, expression):
        expression = expression.strip()
        if not expression:
            return 1
        tokens = self._tokenize(expression)
        if not tokens:
            return 1
        result, _ = self._parse_or(tokens, 0)
        return 0 if result else 1

    def _tokenize(self, expr):
        tokens = []
        i = 0
        while i < len(expr):
            if expr[i] in ' \t':
                i += 1
                continue
            if expr[i] == '(' and i + 1 < len(expr) and expr[i + 1] == '(':
                tokens.append(('dbllparen', '(('))
                i += 2
            elif expr[i] == ')' and i + 1 < len(expr) and expr[i + 1] == ')':
                tokens.append(('dblrparen', '))'))
                i += 2
            elif expr[i:i+2] == '&&':
                tokens.append(('and', '&&'))
                i += 2
            elif expr[i:i+2] == '||':
                tokens.append(('or', '||'))
                i += 2
            elif expr[i:i+2] == '==':
                tokens.append(('eq', '=='))
                i += 2
            elif expr[i:i+2] == '!=':
                tokens.append(('ne', '!='))
                i += 2
            elif expr[i:i+3] == '-eq':
                tokens.append(('int_eq', '-eq'))
                i += 3
            elif expr[i:i+3] == '-ne':
                tokens.append(('int_ne', '-ne'))
                i += 3
            elif expr[i:i+3] == '-lt':
                tokens.append(('int_lt', '-lt'))
                i += 3
            elif expr[i:i+3] == '-gt':
                tokens.append(('int_gt', '-gt'))
                i += 3
            elif expr[i:i+3] == '-le':
                tokens.append(('int_le', '-le'))
                i += 3
            elif expr[i:i+3] == '-ge':
                tokens.append(('int_ge', '-ge'))
                i += 3
            elif expr[i:i+2] == '-f':
                tokens.append(('file_f', '-f'))
                i += 2
            elif expr[i:i+2] == '-d':
                tokens.append(('file_d', '-d'))
                i += 2
            elif expr[i:i+2] == '-e':
                tokens.append(('file_e', '-e'))
                i += 2
            elif expr[i:i+2] == '-r':
                tokens.append(('file_r', '-r'))
                i += 2
            elif expr[i:i+2] == '-w':
                tokens.append(('file_w', '-w'))
                i += 2
            elif expr[i:i+2] == '-x':
                tokens.append(('file_x', '-x'))
                i += 2
            elif expr[i:i+2] == '-n':
                tokens.append(('str_nonempty', '-n'))
                i += 2
            elif expr[i:i+2] == '-z':
                tokens.append(('str_empty', '-z'))
                i += 2
            elif expr[i] == '!':
                tokens.append(('not', '!'))
                i += 1
            elif expr[i] == '(':
                tokens.append(('lparen', '('))
                i += 1
            elif expr[i] == ')':
                tokens.append(('rparen', ')'))
                i += 1
            elif expr[i] == "'":
                j = i + 1
                while j < len(expr) and expr[j] != "'":
                    j += 1
                tokens.append(('string', expr[i + 1:j]))
                i = j + 1
            elif expr[i] == '"':
                j = i + 1
                while j < len(expr) and expr[j] != '"':
                    j += 1
                content = expr[i + 1:j]
                content = self.shell.expand_string(content)
                tokens.append(('string', content))
                i = j + 1
            elif expr[i] == '$':
                expanded, consumed = self.shell._expand_dollar(expr, i)
                if expanded:
                    try:
                        int(expanded)
                        tokens.append(('number', expanded))
                    except ValueError:
                        tokens.append(('string', expanded))
                else:
                    tokens.append(('string', ''))
                i += consumed
            elif expr[i].isdigit():
                j = i
                while j < len(expr) and expr[j].isdigit():
                    j += 1
                tokens.append(('number', expr[i:j]))
                i = j
            elif expr[i].isalpha() or expr[i] == '_' or expr[i] == '/' or expr[i] == '.' or expr[i] == '~':
                j = i
                while j < len(expr) and expr[j] not in ' \t()!&|':
                    if expr[j] in ('"', "'"):
                        break
                    j += 1
                word = expr[i:j]
                expanded = self.shell.expand_string(word)
                tokens.append(('string', expanded))
                i = j
            else:
                i += 1
        return tokens

    def _parse_or(self, tokens, pos):
        left, pos = self._parse_and(tokens, pos)
        while pos < len(tokens) and tokens[pos][0] == 'or':
            pos += 1
            right, pos = self._parse_and(tokens, pos)
            left = left or right
        return left, pos

    def _parse_and(self, tokens, pos):
        left, pos = self._parse_not(tokens, pos)
        while pos < len(tokens) and tokens[pos][0] == 'and':
            pos += 1
            right, pos = self._parse_not(tokens, pos)
            left = left and right
        return left, pos

    def _parse_not(self, tokens, pos):
        if pos < len(tokens) and tokens[pos][0] == 'not':
            pos += 1
            val, pos = self._parse_not(tokens, pos)
            return not val, pos
        return self._parse_primary(tokens, pos)

    def _parse_primary(self, tokens, pos):
        if pos >= len(tokens):
            return False, pos

        tok = tokens[pos]

        if tok[0] == 'lparen':
            pos += 1
            val, pos = self._parse_or(tokens, pos)
            if pos < len(tokens) and tokens[pos][0] == 'rparen':
                pos += 1
            return val, pos

        if tok[0] in ('file_f', 'file_d', 'file_e', 'file_r', 'file_w', 'file_x'):
            return self._eval_file_test(tok[0], tokens, pos)

        if tok[0] == 'str_nonempty':
            pos += 1
            if pos < len(tokens):
                val = tokens[pos][1]
                pos += 1
                return len(val) > 0, pos
            return False, pos

        if tok[0] == 'str_empty':
            pos += 1
            if pos < len(tokens):
                val = tokens[pos][1]
                pos += 1
                return len(val) == 0, pos
            return True, pos

        if pos + 2 <= len(tokens):
            if pos + 1 < len(tokens):
                op = tokens[pos + 1]
                if op[0] in ('eq', 'ne'):
                    left = tokens[pos][1]
                    right = tokens[pos + 2][1] if pos + 2 < len(tokens) else ''
                    pos += 3
                    if op[0] == 'eq':
                        return left == right, pos
                    else:
                        return left != right, pos

                if op[0] in ('int_eq', 'int_ne', 'int_lt', 'int_gt', 'int_le', 'int_ge'):
                    left_str = tokens[pos][1]
                    right_str = tokens[pos + 2][1] if pos + 2 < len(tokens) else '0'
                    try:
                        left = int(left_str)
                    except ValueError:
                        left = 0
                    try:
                        right = int(right_str)
                    except ValueError:
                        right = 0
                    pos += 3
                    if op[0] == 'int_eq':
                        return left == right, pos
                    elif op[0] == 'int_ne':
                        return left != right, pos
                    elif op[0] == 'int_lt':
                        return left < right, pos
                    elif op[0] == 'int_gt':
                        return left > right, pos
                    elif op[0] == 'int_le':
                        return left <= right, pos
                    elif op[0] == 'int_ge':
                        return left >= right, pos

        if tok[0] in ('string', 'number'):
            val = tok[1]
            pos += 1
            if val:
                return True, pos
            return False, pos

        pos += 1
        return False, pos

    def _eval_file_test(self, test_type, tokens, pos):
        pos += 1
        if pos >= len(tokens):
            return False, pos
        path = tokens[pos][1]
        path = os.path.expanduser(path)
        pos += 1
        if test_type == 'file_f':
            return os.path.isfile(path), pos
        elif test_type == 'file_d':
            return os.path.isdir(path), pos
        elif test_type == 'file_e':
            return os.path.exists(path), pos
        elif test_type == 'file_r':
            return os.access(path, os.R_OK), pos
        elif test_type == 'file_w':
            return os.access(path, os.W_OK), pos
        elif test_type == 'file_x':
            return os.access(path, os.X_OK), pos
        return False, pos
