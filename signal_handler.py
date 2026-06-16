import signal
import os
import sys


SIGNAL_MAP = {
    'INT': signal.SIGINT,
    'TERM': signal.SIGTERM,
    'HUP': signal.SIGHUP,
    'QUIT': signal.SIGQUIT,
    'USR1': getattr(signal, 'SIGUSR1', None),
    'USR2': getattr(signal, 'SIGUSR2', None),
    'EXIT': 'EXIT',
    'ERR': 'ERR',
    'DEBUG': 'DEBUG',
}

SIGNAL_NAMES = {v: k for k, v in SIGNAL_MAP.items() if v is not None and v != 'EXIT' and v != 'ERR' and v != 'DEBUG'}


class SignalHandler:
    def __init__(self, shell):
        self.shell = shell
        self.traps = {}
        self._original_handlers = {}

    def set_trap(self, command, sig_name):
        sig_name = sig_name.upper()
        if sig_name.startswith('SIG'):
            sig_name = sig_name[3:]
        if sig_name not in SIGNAL_MAP:
            print(f"minibash: trap: {sig_name}: invalid signal", file=sys.stderr)
            return 1

        sig_key = SIGNAL_MAP[sig_name]
        if command == '':
            self.traps[sig_key] = ('ignore', '')
            if sig_key not in ('EXIT', 'ERR', 'DEBUG') and sig_key is not None:
                try:
                    old = signal.signal(sig_key, signal.SIG_IGN)
                    self._original_handlers[sig_key] = old
                except (OSError, ValueError):
                    pass
        elif command == '-':
            self.traps.pop(sig_key, None)
            if sig_key not in ('EXIT', 'ERR', 'DEBUG') and sig_key is not None:
                try:
                    signal.signal(sig_key, signal.SIG_DFL)
                except (OSError, ValueError):
                    pass
        else:
            self.traps[sig_key] = ('command', command)
            if sig_key not in ('EXIT', 'ERR', 'DEBUG') and sig_key is not None:
                def make_handler(cmd):
                    def handler(signum, frame):
                        self.shell.execute_block(cmd)
                    return handler
                try:
                    old = signal.signal(sig_key, make_handler(command))
                    if sig_key not in self._original_handlers:
                        self._original_handlers[sig_key] = old
                except (OSError, ValueError):
                    pass
        return 0

    def list_traps(self):
        lines = []
        for sig_key, (action, command) in sorted(self.traps.items(), key=lambda x: str(x[0])):
            sig_name = None
            for name, key in SIGNAL_MAP.items():
                if key == sig_key:
                    sig_name = name
                    break
            if sig_name is None:
                sig_name = str(sig_key)
            if action == 'ignore':
                lines.append(f"trap -- '' {sig_name}")
            else:
                lines.append(f"trap -- '{command}' {sig_name}")
        return '\n'.join(lines)

    def trigger_exit(self):
        exit_key = SIGNAL_MAP.get('EXIT')
        if exit_key in self.traps:
            action, command = self.traps[exit_key]
            if action == 'command' and command:
                try:
                    self.shell.execute_block(command)
                except Exception:
                    pass

    def trigger_err(self):
        err_key = SIGNAL_MAP.get('ERR')
        if err_key in self.traps:
            action, command = self.traps[err_key]
            if action == 'command' and command:
                try:
                    self.shell.execute_block(command)
                except Exception:
                    pass

    def trigger_debug(self):
        debug_key = SIGNAL_MAP.get('DEBUG')
        if debug_key in self.traps:
            action, command = self.traps[debug_key]
            if action == 'command' and command:
                try:
                    self.shell.execute_block(command)
                except Exception:
                    pass

    def reset_all(self):
        for sig_key in list(self._original_handlers.keys()):
            if sig_key not in ('EXIT', 'ERR', 'DEBUG') and sig_key is not None:
                try:
                    signal.signal(sig_key, self._original_handlers[sig_key])
                except (OSError, ValueError):
                    pass
        self._original_handlers.clear()
        self.traps.clear()
