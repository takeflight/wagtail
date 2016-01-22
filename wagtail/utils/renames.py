from __future__ import absolute_import, unicode_literals

import sys
import warnings


class RenamedModuleLoader(object):
    """
    A custom module loader that handles renamed modules in a package.

    See PEP 302 for details on how module loaders work.
    """
    def __init__(self, base, module_map, warning):
        self.base = base
        self.module_map = module_map
        self.warning = warning

    def find_module(self, fullname, path=None):
        """
        Should this loader be used to import fullname? This loader is used if
        fullname is an old, renamed module (or a submodule of a module) in the
        module_map.
        """
        if not self._is_submodule(fullname):
            return None
        submodule_path = self._split_submodule(fullname)
        if submodule_path[0] not in self.module_map:
            return None
        return self

    def load_module(self, fullname):
        """
        Load the new module instead of the old, renamed module or submodule
        """
        try:
            return sys.modules[fullname]
        except KeyError:
            pass

        submodule_path = self._split_submodule(fullname)
        old_submodule = submodule_path[0]
        new_submodule = self.module_map[old_submodule]
        new_fullname = '.'.join([self.base, new_submodule] + submodule_path[1:])

        warnings.warn(
            "Module {base}.{old} has been renamed to {base}.{new}. "
            "Update your imports and INSTALLED_APPS".format(
                base=self.base, old=old_submodule, new=new_submodule),
            self.warning, stacklevel=2)

        module = self._load_module(new_fullname)
        sys.modules[fullname] = module
        return module

    def _is_submodule(self, fullname):
        return fullname.startswith(self.base + '.')

    def _split_submodule(self, fullname):
        return fullname[len(self.base) + 1:].split('.')

    def _load_module(self, fullname):
        """
        Load and return the real module
        """
        __import__(fullname)
        return sys.modules[fullname]


def rename_submodules(base, modules, warning):
    sys.meta_path.append(RenamedModuleLoader(base, modules, warning))
