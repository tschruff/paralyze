import codecs


def str_or_file(f, callback, mode='r', encoding='utf-8', *args, **kwargs):
    if isinstance(f, str):
        with codecs.open(f, mode, encoding=encoding) as f:
            return callback(f, *args, **kwargs)
    else:
        return callback(f, *args, **kwargs)
