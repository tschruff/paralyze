import posixpath
import jinja2


class RemoteFileSystemLoader(jinja2.BaseLoader):

    def __init__(self, sftp, *search_path, encoding='utf-8', follow_links=False):
        self._sftp = sftp
        self._path = search_path
        self._enc = encoding
        self._follow_links = follow_links

    def get_source(self, environment, template):
        for path in self._path:
            result = self._get_source(path, environment, template)
            if len(result):
                return result
        raise jinja2.TemplateNotFound(template)

    def _get_source(self, path, environment, template):
        path = posixpath.join(path, template)
        if not self._path_exists(path):
            return ()
        mtime = self._get_stat(path).st_mtime
        with self._sftp.file(path, 'r') as f:
            source = f.read().decode('utf-8')
        return source, path, lambda: mtime == self._get_stat(path).st_mtime

    def _path_exists(self, path):
        try:
            self._get_stat(path)
            return True
        except IOError:
            return False

    def _get_stat(self, path):
        if self._follow_links:
            return self._sftp.stat(path)
        else:
            return self._sftp.lstat(path)
