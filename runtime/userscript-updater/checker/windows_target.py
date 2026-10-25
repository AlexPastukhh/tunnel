"""Shared Win32 file operations; each caller supplies its own checked destination scope."""



class WindowsFileOperations:
    def read(self, root, relative):
        try:
            return self.io.read(self.path(root, relative))
        except OSError as exc:
            if exc.errno in (2, 3):
                return None
            raise

    def metadata(self, root, relative):
        return self.io.metadata(self.path(root, relative))

    def replace(self, root, relative, data, metadata, *, expected_sha256):
        self.io.write(self.path(root, relative), data, metadata, expected_sha256)

    def remove(self, root, relative, *, expected_sha256, expected_metadata=None):
        self.io.remove(self.path(root, relative), expected_sha256, expected_metadata)

    def mkdir(self, root, relative):
        return self.io.mkdir(self.path(root, relative))

    def rmdir_if_owned_empty(self, root, relative, identity):
        self.io.rmdir_if_owned_empty(self.path(root, relative), identity)
