import re


class HeredocParser:
    def __init__(self, shell):
        self.shell = shell

    def parse_heredoc_line(self, line):
        result = self._find_heredoc_redirect(line)
        if result is not None:
            return result
        result = self._find_hered_string(line)
        if result is not None:
            return result
        return None

    def _find_heredoc_redirect(self, line):
        idx = line.find('<<')
        if idx == -1:
            return None
        if idx > 0 and line[idx - 1] == '<':
            return None
        after = idx + 2
        if after < len(line) and line[after] == '<':
            return None
        if after < len(line) and line[after] == '-':
            strip_tabs = True
            after += 1
        else:
            strip_tabs = False
        while after < len(line) and line[after] in ' \t':
            after += 1
        delimiter_start = after
        while after < len(line) and line[after] not in ' \t\n;|&><':
            after += 1
        delimiter = line[delimiter_start:after]
        if not delimiter:
            return None
        no_expand = False
        if (delimiter.startswith("'") and delimiter.endswith("'")) or \
           (delimiter.startswith('"') and delimiter.endswith('"')):
            no_expand = True
            delimiter = delimiter[1:-1]
        cmd_part = line[:idx].rstrip()
        return {
            'type': 'heredoc',
            'delimiter': delimiter,
            'strip_tabs': strip_tabs,
            'no_expand': no_expand,
            'cmd_part': cmd_part,
            'rest': line[after:]
        }

    def _find_hered_string(self, line):
        idx = line.find('<<<')
        if idx == -1:
            return None
        after = idx + 3
        while after < len(line) and line[after] in ' \t':
            after += 1
        string_content = line[after:].strip()
        cmd_part = line[:idx].rstrip()
        no_expand = False
        if string_content.startswith("'") and string_content.endswith("'"):
            content = string_content[1:-1]
            no_expand = True
        elif string_content.startswith('"') and string_content.endswith('"'):
            content = string_content[1:-1]
            no_expand = False
        else:
            content = string_content
            no_expand = False
        return {
            'type': 'herestring',
            'content': content,
            'no_expand': no_expand,
            'cmd_part': cmd_part
        }

    def collect_heredoc_body(self, lines, start_index, delimiter, strip_tabs):
        body_lines = []
        i = start_index
        while i < len(lines):
            raw = lines[i].rstrip('\n')
            check = raw.strip() if strip_tabs else raw
            if check == delimiter:
                return body_lines, i + 1
            if strip_tabs:
                raw = raw.lstrip('\t')
            body_lines.append(raw)
            i += 1
        return body_lines, i

    def process_script_lines(self, lines):
        processed = []
        pending_heredocs = []
        i = 0
        while i < len(lines):
            raw = lines[i].rstrip('\n')
            stripped = raw.strip()
            if not stripped or stripped.startswith('#'):
                processed.append(raw)
                i += 1
                continue
            full_line = raw
            while full_line.rstrip().endswith('\\') and i + 1 < len(lines):
                i += 1
                full_line = full_line.rstrip()[:-1] + ' ' + lines[i].rstrip('\n')
            heredoc_info = self.parse_heredoc_line(full_line)
            if heredoc_info is not None and heredoc_info['type'] == 'heredoc':
                delimiter = heredoc_info['delimiter']
                strip_tabs = heredoc_info['strip_tabs']
                no_expand = heredoc_info['no_expand']
                cmd_part = heredoc_info['cmd_part']
                body_lines, i = self.collect_heredoc_body(lines, i + 1, delimiter, strip_tabs)
                placeholder = f"__HEREDOC_{len(pending_heredocs)}__"
                pending_heredocs.append({
                    'placeholder': placeholder,
                    'type': 'heredoc',
                    'body_lines': body_lines,
                    'no_expand': no_expand
                })
                processed.append(f"{cmd_part} << {placeholder}")
            elif heredoc_info is not None and heredoc_info['type'] == 'herestring':
                content = heredoc_info['content']
                no_expand = heredoc_info['no_expand']
                cmd_part = heredoc_info['cmd_part']
                placeholder = f"__HERESTRING_{len(pending_heredocs)}__"
                pending_heredocs.append({
                    'placeholder': placeholder,
                    'type': 'herestring',
                    'content': content,
                    'no_expand': no_expand
                })
                processed.append(f"{cmd_part} <<< {placeholder}")
            else:
                processed.append(full_line)
            i += 1
        return processed, pending_heredocs

    def resolve_heredoc_data(self, pending_heredocs):
        data = {}
        for item in pending_heredocs:
            placeholder = item['placeholder']
            if item['type'] == 'heredoc':
                body_lines = item['body_lines']
                no_expand = item['no_expand']
                if no_expand:
                    content = '\n'.join(body_lines) + '\n'
                else:
                    expanded_lines = [self.shell.expand_string(line) for line in body_lines]
                    content = '\n'.join(expanded_lines) + '\n'
                data[placeholder] = content
            elif item['type'] == 'herestring':
                content = item['content']
                no_expand = item['no_expand']
                if not no_expand:
                    content = self.shell.expand_string(content)
                data[placeholder] = content + '\n'
        return data
