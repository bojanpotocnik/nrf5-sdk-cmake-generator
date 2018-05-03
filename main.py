"""
Generate CMake for Nordic nRF5 SDK which can then be included in custom projects via:
    `TODO: what command?`

Usage:
    python3 main.py "NRF5_SDK_ROOT"

    Arguments (shall be enclosed in "" if containing spaces):
        NRF5_SDK_ROOT : Root directory of the nRF5 SDK, that is directory
                        containing subdirectories components, examples,
                        external, ...
"""
import io
import os
from pathlib import Path
from typing import Optional, Dict, Union

import pymake.pymake.parser
import pymake.pymake.parserdata
from pymake import pymake

__author__ = "Bojan Potočnik"


def create_file(cmake_version: str = "3.0.0") -> io.StringIO:
    f = io.StringIO()
    write_line(f, "# CMake file made by Nordic nRF5 SDK CMake Generator")
    write_line(f, "# https://github.com/bojanpotocnik/nrf5-sdk-cmake-generator.git")
    write_line(f, "cmake_minimum_required(VERSION {})".format(cmake_version))
    write_line(f)
    return f


def cmake_set_variable(name: str, value: Union[Dict, str, Path],
                       cache_path: Optional[str] = None, force: bool = False) -> str:
    if isinstance(value, dict):
        value = value[name]
    if isinstance(value, Path):
        value = str(value.as_posix())
    return "set({} {}{}{})".format(name, value,
                                   ' CACHE PATH "{}"'.format(cache_path) if cache_path else "",
                                   " FORCE" if force else "")


def write_line(f: io.StringIO, line: Optional[str] = None):
    f.write((line or "") + "\n")


def generate_cmake_for_makefile(makefile_path: Path, print_ignored: bool = True) -> bool:
    with open(makefile_path, 'r') as f:
        makefile = f.read()

    # Performance improvement.
    # PROJECT_NAME is required variable in Makefiles of interest and this is much faster than parsing with pymake.
    if "PROJECT_NAME" not in makefile:
        return False

    # Parse all Makefile statements
    makefile_statements: pymake.parserdata.StatementList = pymake.parser.parsestring(makefile, makefile_path)

    # These are Makefile variables of interest.
    variable_names = (
        "PROJECT_NAME", "TARGETS",
        "SDK_ROOT", "PROJ_DIR", "TEMPLATE_PATH",
        "LINKER_SCRIPT",
        "SRC_FILES", "INC_FOLDERS", "LIB_FILES",
        "OPT",
        "CFLAGS", "CXXFLAGS", "ASMFLAGS", "LDFLAGS",
        "LIB_FILES"
    )

    # Extracted useful statements.
    statements: Dict[str, pymake.parserdata.SetVariable] = {}

    # Search trough all statements in the Makefile and keep all of interest.
    for statement in makefile_statements:
        if not isinstance(statement, pymake.parserdata.SetVariable):
            continue
        name = statement.name()
        if name in variable_names:
            statements[name] = statement

    # This Makefile is not relevant if it does not contain certain required variables.
    if any((name not in statements) for name in ("PROJECT_NAME", "SRC_FILES", "INC_FOLDERS", "CFLAGS", "LDFLAGS")):
        if print_ignored:
            print("Ignoring '{}'".format(makefile_path))
        else:
            print(".", end="", flush=True)
        return False
    print("\nProcessing '{}'".format(makefile_path))

    f = create_file("2.4.0")
    write_line(f, cmake_set_variable("PROJECT_NAME", statements["PROJECT_NAME"].value))
    write_line(f)
    write_line(f, cmake_set_variable("TARGETS", statements["TARGETS"].value))
    write_line(f)
    write_line(f, cmake_set_variable("SDK_ROOT", statements["SDK_ROOT"].value))
    write_line(f, cmake_set_variable("PROJ_DIR", statements["PROJ_DIR"].value))
    write_line(f)
    write_line(f, "# Source files common to all targets")
    write_line(f, cmake_set_variable("SRC_FILES", statements["SRC_FILES"].value))
    write_line(f)
    write_line(f, "# Include folders common to all targets")
    write_line(f, cmake_set_variable("INC_FOLDERS", statements["INC_FOLDERS"].value))
    write_line(f)
    write_line(f, "# Libraries common to all targets")
    write_line(f, cmake_set_variable("LIB_FILES", statements["LIB_FILES"].value))
    write_line(f)
    write_line(f, "# Optimization flags")
    write_line(f, cmake_set_variable("OPT", statements["OPT"].value))
    write_line(f, "# Uncomment the line below to enable link time optimization")
    write_line(f, "# OPT += -flto")
    write_line(f)
    write_line(f)
    write_line(f, "# C flags common to all targets")
    write_line(f, cmake_set_variable("CFLAGS", statements["CFLAGS"].value))
    write_line(f)
    write_line(f, "# C++ flags common to all targets")
    write_line(f, cmake_set_variable("CXXFLAGS", statements["CXXFLAGS"].value))
    write_line(f)
    write_line(f, "# Assembler flags common to all targets")
    write_line(f, cmake_set_variable("ASMFLAGS", statements["ASMFLAGS"].value))
    write_line(f)
    write_line(f, "# Linker flags")
    write_line(f, cmake_set_variable("LDFLAGS", statements["LDFLAGS"].value))
    write_line(f)
    write_line(f)
    write_line(f, "project(${PROJECT_NAME})")
    write_line(f)
    write_line(f, 'list(APPEND CFLAGS "-undef" "-D__GNUC__")')
    write_line(f, "list(FILTER CFLAGS EXCLUDE REGEX mcpu)")
    write_line(f, 'string(REPLACE ";" " " CFLAGS "${CFLAGS}")')
    write_line(f, "set(CMAKE_C_FLAGS ${CFLAGS})")
    write_line(f)
    write_line(f, "include_directories(${INC_FOLDERS})")
    write_line(f)
    write_line(f, "add_executable(${PROJECT_NAME} ${SRC_FILES})")
    write_line(f)

    # Replace string expansions from Make to CMake syntax.
    s: str = f.getvalue()
    for name in variable_names:
        # When using str.format, "{{" and "}}" is used to print "{" and "}", that is why there are {{+{ below.
        s = s.replace("$({})".format(name), "${{{}}}".format(name))

    with open(makefile_path.parent.joinpath("CMakeLists.txt"), 'w') as cmake_f:
        cmake_f.write(s)

    return True


def generate_cmake_for_examples(sdk_root: Path) -> int:
    f = create_file("2.8.9")
    write_line(f, "# Configure toolchain")
    write_line(f, "include(arm-gcc-toolchain.cmake)")
    write_line(f)
    # Go trough all makefiles in all of the SDK subdirectories.
    for dir_path, dir_names, filenames in os.walk(str(sdk_root)):
        dir_path = Path(dir_path)
        for filename in filenames:
            if filename == "Makefile":
                if generate_cmake_for_makefile(dir_path.joinpath(filename)):
                    write_line(f, "#add_subdirectory(./{})".format(dir_path.relative_to(sdk_root).as_posix()))
    write_line(f)

    with open(sdk_root.joinpath("CMakeLists.txt"), 'w') as cmake_f:
        cmake_f.write(f.getvalue())

    return 0


def generate_common_cmakes(gcc_root: Path, gcc_prefix: str, gcc_extension: str, sdk_root: Path) -> None:
    f = create_file("2.4.0")
    write_line(f, "#")
    write_line(f, "# GCC Compiler")
    write_line(f, "#")
    write_line(f, "# Path to the directory where GCC Compiler (*gcc*) is located, including trailing '/':")
    write_line(f, cmake_set_variable("ARM_TOOLCHAIN_DIR", gcc_root.as_posix() + "/"))
    write_line(f, "# Prefix and postfix (extension) to use when invoking GCC tools "
                  "({prefix}gcc{extension}, {prefix}ld{extension}, ...):")
    write_line(f, cmake_set_variable("ARM_TOOLCHAIN_PREFIX", gcc_prefix))
    write_line(f, cmake_set_variable("ARM_TOOLCHAIN_EXTENSION", gcc_extension))
    write_line(f)
    write_line(f, "#")
    write_line(f, "# nRF5 SDK")
    write_line(f, "#")
    write_line(f, cmake_set_variable("NRF5_SDK_ROOT", sdk_root.relative_to(sdk_root)))
    write_line(f)

    with open(sdk_root.joinpath("paths.cmake"), 'w') as cmake_f:
        cmake_f.write(f.getvalue())

    f = create_file("2.4.0")
    write_line(f, "include(CMakeForceCompiler)")
    write_line(f, cmake_set_variable("CMAKE_SYSTEM_NAME", "Generic"))
    write_line(f, cmake_set_variable("CMAKE_SYSTEM_PROCESSOR", "ARM"))
    write_line(f)
    write_line(f, "# Include machine specific path configuration.")
    write_line(f, "# Requires definition of:")
    write_line(f, "#   ARM_TOOLCHAIN_DIR")
    write_line(f, "#   ARM_TOOLCHAIN_PREFIX")
    write_line(f, "include(paths.cmake)")
    write_line(f)
    write_line(f, "if (DEFINED PROJECT_NAME)")
    write_line(f, '    message(FATAL_ERROR "Toolchain must be set before any language is set '
                  '(i.e. before any project() or enable_language() command).")')
    write_line(f, "endif ()")
    write_line(f)
    write_line(f, cmake_set_variable("CMAKE_C_COMPILER",
                                     "${ARM_TOOLCHAIN_DIR}${ARM_TOOLCHAIN_PREFIX}gcc${ARM_TOOLCHAIN_EXTENSION}",
                                     "C Compiler (gcc)", True))
    write_line(f, cmake_set_variable("CMAKE_CXX_COMPILER",
                                     "${ARM_TOOLCHAIN_DIR}${ARM_TOOLCHAIN_PREFIX}g++${ARM_TOOLCHAIN_EXTENSION}",
                                     "C++ Compiler (g++)", True))
    write_line(f, cmake_set_variable("CMAKE_ASM_COMPILER", "${CMAKE_C_COMPILER}",
                                     "ASM Compiler (gcc)", True))
    write_line(f, cmake_set_variable("CMAKE_OBJCOPY",
                                     "${ARM_TOOLCHAIN_DIR}${ARM_TOOLCHAIN_PREFIX}objcopy${ARM_TOOLCHAIN_EXTENSION}",
                                     "objcopy tool", True))
    write_line(f, cmake_set_variable("CMAKE_OBJDUMP",
                                     "${ARM_TOOLCHAIN_DIR}${ARM_TOOLCHAIN_PREFIX}objdump${ARM_TOOLCHAIN_EXTENSION}",
                                     "objdump tool", True))
    write_line(f, cmake_set_variable("CMAKE_SIZE_UTIL",
                                     "${ARM_TOOLCHAIN_DIR}${ARM_TOOLCHAIN_PREFIX}size${ARM_TOOLCHAIN_EXTENSION}",
                                     "size tool tool", True))
    write_line(f)
    write_line(f, "message(\"Using C compiler: '${CMAKE_C_COMPILER}'\")")
    write_line(f, "message(\"Using C++ compiler: '${CMAKE_CXX_COMPILER}'\")")
    write_line(f)
    write_line(f)
    write_line(f, "# Without that flag CMake is not able to pass test compilation check "
                  "(only for successful compilation of CMake test)")
    write_line(f, cmake_set_variable("CMAKE_EXE_LINKER_FLAGS_INIT", '"--specs=nosys.specs"'))
    write_line(f)
    # write_line(f, "# set(CMAKE_FIND_ROOT_PATH ${ARM_TOOLCHAIN_DIR})")
    # write_line(f, "# set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)")
    # write_line(f, "# set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)")
    # write_line(f, "# set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)")

    with open(sdk_root.joinpath("arm-gcc-toolchain.cmake"), 'w') as cmake_f:
        cmake_f.write(f.getvalue())


def main() -> int:
    import argparse
    import distutils.spawn

    # Help user by detecting default values.
    sdk_root = os.environ.get("NRF5_SDK_ROOT") or os.environ.get("NRF52_SDK_ROOT") or os.environ.get("NRF_SDK_ROOT")
    gcc = distutils.spawn.find_executable("arm-none-eabi-gcc")
    nrfjprog = distutils.spawn.find_executable("nrfjprog")

    # region Parse arguments

    parser = argparse.ArgumentParser(
        description="Generate CMake files for Nordic nRF5 SDK."
    )
    # nargs='+' is used to enable providing value containing spaces.
    parser.add_argument("--sdk", dest="NRF5_SDK_ROOT", type=str, nargs='+',
                        default=sdk_root, required=not bool(sdk_root),
                        help="Root directory of the nRF5 SDK (directory containing subdirectories "
                             "components, config, examples, external). Can be omitted if "
                             "NRF[5[2]]_SDK_ROOT environmental variable is defined."
                             + (" (detected: {})".format(sdk_root) if sdk_root else ""))
    parser.add_argument("--gcc", dest="GCC", type=str, nargs='+',
                        default=gcc, required=not bool(gcc),
                        help="Path to the GCC executable of the GNU ARM Embedded Toolchain. This path will "
                             "also be used to find other tools (g++, ld, objcopy, objdump, size)."
                             + (" (detected: {})".format(gcc) if gcc else ""))
    parser.add_argument("--prog", dest="NRFJPROG", type=str, nargs='+', default=nrfjprog,
                        help="Path to the nrfjprog executable (part of the nRF5x Command Line Tools provided "
                             "by Nordic). If not provided then targets (flash and erase) are not generated."
                             + (" (detected: {})".format(nrfjprog) if nrfjprog else ""))
    parser.add_argument("--config", type=str, nargs='+', dest="SDK_CONFIG",
                        help="SDK configuration file (usually 'sdk_config.h') used to include (only) header and "
                             "source files for used/enabled modules. If not provided then source files for "
                             "all modules are added to the CMake file.")
    parser.add_argument("-e", "--examples", action='store_true', dest="EXAMPLES",
                        help="If provided then CMake files are generated for all example projects in the SDK "
                             "and --config is ignored.")

    # args = parser.parse_args(["--help"])
    # args = parser.parse_args()
    # args = parser.parse_args(r'--sdk G:\Git\Dia-Vit\FW\nRF5_SDK --prog "C:\D ff\222 3\x.exe" -e'.split(" "))
    # args = parser.parse_args(r'--sdk G:\Git\Dia-Vit\FW\nRF5_SDK --prog "C:\f\2223\x.exe" -e'.split(" "))
    args = parser.parse_args(r'--sdk G:\Git\nRF5_SDK -e'.split(" "))
    args = vars(args)

    # endregion Parse arguments

    # region Check parameters

    # Provided arguments have higher priority - however keep defaults if argument is not provided.
    # Argument value will always be a list because of nargs='+'.
    if args["NRF5_SDK_ROOT"] is not None:
        sdk_root: Optional[str] = "".join(args["NRF5_SDK_ROOT"]).strip('"')
    if args["GCC"] is not None:
        gcc: Optional[str] = "".join(args["GCC"]).strip('"')
    if args["NRFJPROG"] is not None:
        nrfjprog: Optional[str] = "".join(args["NRFJPROG"]).strip('"') or None
    sdk_config: Optional[str] = "".join(args["SDK_CONFIG"] or ()).strip('"') or None
    examples: bool = args["EXAMPLES"]

    # sdk_root shall be provided (handled by argparse).
    sdk_root: Path = Path(sdk_root)
    if not (sdk_root.is_dir() and sdk_root.joinpath("components").is_dir() and sdk_root.joinpath("external").is_dir()):
        print("NRF5_SDK_ROOT shall be directory containing at least 'components' and 'external' subdirectories.")
        return -1

    # gcc shall be provided (handled by argparse).
    gcc = Path(gcc)
    # Detect prefix. GCC is always "gcc", but it can have ".exe" extension and can have any (or no) prefix.
    gcc_prefix = gcc.stem.rstrip("gcc")
    gcc_extension = gcc.suffix
    gcc_root = gcc.parent
    # Build paths for other tools.
    gpp = gcc_root.joinpath(gcc_prefix + "g++" + gcc_extension)
    ld = gcc_root.joinpath(gcc_prefix + "ld" + gcc_extension)
    objcopy = gcc_root.joinpath(gcc_prefix + "objcopy" + gcc_extension)
    objdump = gcc_root.joinpath(gcc_prefix + "objdump" + gcc_extension)
    size = gcc_root.joinpath(gcc_prefix + "size" + gcc_extension)

    if not all(os.access(str(exe), os.X_OK) for exe in (gcc, gpp, ld, objcopy, objdump, size)):
        print("GCC shall be valid path to the GNU ARM Embedded Toolchain 'gcc' executable, next to which "
              "shall also be located g++, ld, objcopy, objdump and size tools with the same prefix and extension.")
        return -2

    # nrfjprog shall be valid if provided.
    if nrfjprog and not os.access(nrfjprog, os.X_OK):
        print("Path to the nrfjprog executable ('{}') is invalid.".format(nrfjprog))
        return -3

    # sdk_config shall be header file if provided.
    if sdk_config and not os.access(sdk_config, os.R_OK):
        print("Path to the sdk_config.h file ('{}') is invalid.".format(sdk_config))
        return -4

    # endregion Check parameters

    generate_common_cmakes(gcc_root, gcc_prefix, gcc_extension, sdk_root)

    if examples:
        generate_cmake_for_examples(sdk_root)
    else:
        pass
        # TODO: generate_cmake()

    return 0


if __name__ == "__main__":
    ret = main()
    if ret != 0:
        print()
        input("Press any key to continue...")
    exit(ret)
