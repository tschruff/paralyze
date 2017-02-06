

def get_input(prompt, default=None, options=()):
    value = input('>> %s %s: [%s] ' % (prompt, '/'.join(map(str, options)), str(default or '-'))) or default
    if default:
        return type(default)(value)
    return value
