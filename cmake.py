import io
import os
import shutil
import time
from pathlib import Path
from typing import Optional, Union, Dict

__author__ = "Bojan Potočnik"
__remote__ = "https://github.com/bojanpotocnik/nrf5-sdk-cmake-generator.git"


class CMake(io.StringIO):
    """Class representing CMake file."""

    def __init__(self, minimum_version: Optional[str] = "3.7", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.writeline("# For bug reports and improvements please navigate to")
        self.writeline("# " + __remote__)
        if minimum_version:
            self.writeline("cmake_minimum_required(VERSION {})".format(minimum_version))
        self.writeline()

    def save(self, path: Union[None, str, Path], *,
             block_until_saved: bool = True, raise_warning: bool = True, print_success: bool = True) -> bool:
        """
        Try to save file and eventually keep trying if save operation is blocked by OS. Useful if some
        file is opened for write in other program and save operation fails until the file is saved or closed.

        :param path:              Path on the disk where the file will be generated
                                  (existing files will be overwritten).
        :param block_until_saved: Whether this function will block until the file is successfully saved.
        :param raise_warning:     Whether to print warnings if save fails.
        :param print_success:     Whether to print result of the operation.

        :return: `True` if the file was successfully saved.
        """
        path = os.path.realpath(path)

        path_temp = path + ".tmp"
        path_backup = path + ".bak"

        # 1. Write to a temporary file.
        with open(path_temp, 'w') as f:
            # What is the best way to write the contents of a StringIO to a file?
            #   https://stackoverflow.com/a/3253819/5616255
            self.seek(0)
            # noinspection PyTypeChecker
            shutil.copyfileobj(self, f, -1)
            # # 2. Flush and sync the file.
            # f.flush()
            # os.fsync(f.fileno())

        # 3. Make a backup of the original file (if exists).
        try:
            shutil.copy2(path, path_backup)
        except FileNotFoundError:
            pass

        # 4. Rename/copy the temporary file over the original file.
        while True:
            try:
                os.replace(path_temp, path)
                success = True
                break
            except PermissionError:
                if raise_warning:
                    print("Cannot save file '{}' - it is probably opened somewhere".format(path))
                if not block_until_saved:
                    success = False
                    break
            time.sleep(1)

        # 5. Delete a backup file.
        try:
            os.remove(path_backup)
        except FileNotFoundError:
            pass

        if print_success:
            if success:
                print("Saved file '{}'".format(path))
            else:
                print("Could not save file '{}'".format(path))

        return success

    # noinspection SpellCheckingInspection
    def writeline(self, line: Optional[str] = None) -> 'CMake':
        self.write((line or "") + "\n")
        return self

    def __add__(self, other: Union['CMake', str]) -> 'CMake':
        if isinstance(other, type(self)):
            other = other.getvalue()
        elif not isinstance(other, str):
            return NotImplemented

        obj = type(self)()
        obj.write(self.getvalue())
        obj.write(other)
        return obj

    def __iadd__(self, other: Union['CMake', str]) -> 'CMake':
        # noinspection SpellCheckingInspection
        """Shortcut for the :meth:`writeline` method."""
        if isinstance(other, str):
            pass
        elif isinstance(other, type(self)):
            other = other.getvalue()
        else:
            return NotImplemented

        self.writeline(other)
        return self

    def set(self, variable_name: str, value: Union[Dict[str, str], str, Path], enclose_value_in_quotes: bool = False) \
            -> 'CMake':
        """
        Add line `set(variable_name variable_value)` or `set(variable_name "variable_value")`.

        :param variable_name: CMake variable name.
        :param value: Variable value.\n
                      If dictionary then `variable_name` key will be used to retrieve the value.\n
                      If `Path` then :meth:`.as_posix` will be called and converted to string.
        :param enclose_value_in_quotes: Whether to enclose the value in quotes. Automatically set to `True` if
                                        Path is provided as value.
        """
        if isinstance(value, dict):
            value = value[variable_name]
        if isinstance(value, Path):
            value = str(value.as_posix())
            enclose_value_in_quotes = True

        if enclose_value_in_quotes:
            value = '"' + value + '"'

        self.writeline("set({} {})".format(variable_name, value))
        return self

    def convert_variable_expansion(self, text: Optional[str] = None) -> str:
        """
        Replace variable expansion from Make `$(VARIABLE)` syntax to CMake `${VARIABLE}` syntax.

        :param text: Text in which to
        """
        # Replace string expansions from Make to CMake syntax.

        s: str = f.getvalue()
        for name in variable_names:
            # When using str.format, "{{" and "}}" is used to print "{" and "}", that is why there are {{+{ below.
            s = s.replace("$({})".format(name), "${{{}}}".format(name))

        pass


def _test() -> None:
    cmake = CMake()
    cmake += "# Test CMake file"
    cmake.set("SOME_VARIABLE", "Variable/value/not/quoted")
    cmake.set("SOME_VARIABLE", "Variable/value with quotes", True)
    # noinspection SpellCheckingInspection
    cmake.writeline("# Test line with .writeline()")
    cmake += ""
    cmake.writeline()
    cmake += "# End - before save 1"
    cmake.save("TestCmake1.txt")

    cmake += "# Start - before save 2"
    cmake.save("TestCmake2.txt")

    cmake += "# Start - before save 3"
    cmake.save("TestCmake3.txt")


if __name__ == "__main__":
    _test()
