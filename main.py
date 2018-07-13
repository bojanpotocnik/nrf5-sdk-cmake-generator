import os
from pathlib import Path
from typing import Optional, Dict, Union

import pymake.pymake.parser
import pymake.pymake.parserdata
from cmake import CMake
from pymake import pymake

__author__ = "Bojan Potočnik"


def generate_common_cmakes(gcc_path: Path, sdk_root: Path, nrfjprog_path: Optional[Path]) -> None:
    import socket

    toolchain_file_path = sdk_root.joinpath("toolchain.cmake")

    # region Machine specific file with paths

    # 2.6.3 to prevent "Policy CMP0011 is not set" warning (https://cmake.org/cmake/help/v3.0/policy/CMP0011.html).
    cmake = CMake("2.6.3")
    cmake += "# Path to the GNU GCC Compiler (usually [arm-none-eabi-]gcc[.exe]):"
    cmake.set("GCC_PATH", gcc_path)
    # Replace the last occurrence of "gcc" with "g++" to "retrieve" the path for C++ compiler.
    # https://stackoverflow.com/a/2556252/5616255
    cmake.set("CPP_PATH", Path("g++".join(str(gcc_path).rsplit("gcc", 1))))
    cmake += ""
    cmake += "# Root directory of the nRF5 SDK"
    cmake.set("NRF5_SDK_ROOT", sdk_root)
    if nrfjprog_path:
        cmake += ""
        cmake += "# Path to the nrfjprog executable (part of the nRF5x Command Line Tools provided by Nordic)"
        cmake.set("NRFJPROG", nrfjprog_path)

    cmake += ""
    print("# Saving CMake script with paths definitions...")
    cmake.save(toolchain_file_path.parent.joinpath("paths.{}.cmake".format(socket.getfqdn())))
    del cmake
    # endregion Machine specific file with paths

    # region Toolchain file for CMake cross-compiling

    # Generate a toolchain file for CMake cross-compiling
    # https://gitlab.kitware.com/cmake/community/wikis/doc/cmake/CrossCompiling
    # https://cmake.org/cmake/help/v3.6/manual/cmake-toolchains.7.html
    cmake = CMake()
    cmake += "# The CMake toolchain file. Pass it as -DCMAKE_TOOLCHAIN_FILE parameter when invoking CMake."
    cmake += "#     `cmake -DCMAKE_TOOLCHAIN_FILE={} ...`".format(toolchain_file_path)
    cmake += "# or"
    cmake += "#     `cmake -DCMAKE_TOOLCHAIN_FILE={} ...`".format(toolchain_file_path.name)
    cmake += "# Read more at: https://gitlab.kitware.com/cmake/community/wikis/doc/cmake/CrossCompiling"
    cmake += "#               https://cmake.org/cmake/help/v3.6/manual/cmake-toolchains.7.html"
    cmake += ""
    cmake += "# Include machine specific path configuration"
    cmake += ("# Hostname (HOSTNAME) is the name of the computer. "
              "Fully qualified domain name (FQDN) is the hostname plus the domain")
    cmake += ("# company uses, often ending in .local "
              "(e.g. bojan.my-company.com or bojan.my-company.local if the company does not")
    cmake += "# use an external internet domain name)."
    cmake += "cmake_host_system_information(RESULT PC_NAME QUERY FQDN)"
    cmake.set("PATHS_FN", "paths.${PC_NAME}.cmake", True)
    cmake += ("message(\"Searching for machine specific path configuration "
              "in '${CMAKE_CURRENT_LIST_DIR}/${PATHS_FN}'...\")")
    cmake += "include(\"${CMAKE_CURRENT_LIST_DIR}/${PATHS_FN}\")"
    cmake += ""

    cmake += "# Specify the target system"
    # CMAKE_SYSTEM_NAME : this one is mandatory, it is the name of the target system, i.e. the same as
    # CMAKE_SYSTEM_NAME would have if CMake would run on the target system. If your target is an embedded
    # system without OS set CMAKE_SYSTEM_NAME to "Generic".
    cmake.set("CMAKE_SYSTEM_NAME", "Generic")
    # CMAKE_SYSTEM_PROCESSOR : optional, processor (or hardware) of the target system.
    cmake.set("CMAKE_SYSTEM_PROCESSOR", "ARM")
    cmake += ""
    cmake += "# Specify the cross compiler"
    # CMAKE_C_COMPILER : the C compiler executable, may be the full path or just the filename. If it is specified with
    # full path, then this path will be preferred when searching the C++ compiler and the other tools (binutils,
    # linker, etc.). If this compiler is a gcc-cross compiler with a prefixed name (e.g. "arm-elf-gcc") CMake will
    # detect this and automatically find the corresponding C++ compiler (i.e. "arm-elf-c++").
    cmake.set("CMAKE_C_COMPILER", "${GCC_PATH}")
    # CMAKE_CXX_COMPILER : the C++ compiler executable, may be the full path or just the filename. It is handled the
    # same way as CMAKE_C_COMPILER. If the toolchain is a GNU toolchain, you only need to set one of both.
    cmake.set("CMAKE_CXX_COMPILER", "${CPP_PATH}")
    # CMAKE_FIND_ROOT_PATH : this is a list of directories, each of the directories listed there will be prepended
    # to each of the search directories of every FIND_XXX() command.
    cmake += ""
    cmake += "# Set the target environment location"
    # CMAKE_FIND_ROOT_PATH : this is a list of directories, each of the directories listed there will be prepended to
    # each of the search directories of every FIND_XXX() command. So e.g. if your target environment is installed
    # under /opt/eldk/ppc_74xx, set CMAKE_FIND_ROOT_PATH to this directory. Then e.g. FIND_LIBRARY(BZ2_LIB bz2) will
    # search in /opt/eldk/ppc_74xx/lib, /opt/eldk/ppc_74xx/usr/lib, /lib, /usr/lib and so give
    # /opt/eldk/ppc_74xx/usr/lib/libbz2.so as result.
    # gcc is usually located in the 'bin 'directory (1st .parent) in the toolchain root (2nd .parent).
    cmake += 'list(APPEND CMAKE_FIND_ROOT_PATH "{}")'.format(str(gcc_path.parent.parent.as_posix()))
    cmake += "list(APPEND CMAKE_FIND_ROOT_PATH ${NRF5_SDK_ROOT})"
    cmake += ""
    # CMAKE_FIND_ROOT_PATH_MODE_PROGRAM controls whether the CMAKE_FIND_ROOT_PATH and CMAKE_SYSROOT are used
    # by find_program(). If set to NEVER, then the roots in CMAKE_FIND_ROOT_PATH will be ignored and only
    # the host system root will be used.
    cmake += "# Search for programs in the build host directories"
    cmake.set("CMAKE_FIND_ROOT_PATH_MODE_PROGRAM", "NEVER")

    cmake += "# Search for libraries and headers in the target directories"
    cmake.set("CMAKE_FIND_ROOT_PATH_MODE_LIBRARY", "ONLY")
    cmake.set("CMAKE_FIND_ROOT_PATH_MODE_INCLUDE", "ONLY")
    cmake.set("CMAKE_FIND_ROOT_PATH_MODE_PACKAGE", "ONLY")

    # TODO: Is the following required?
    # cmake += ""
    # cmake += "# Without that flag CMake is not able to pass test compilation check " \
    #          "(only for successful compilation of CMake test)"
    # cmake.set("CMAKE_EXE_LINKER_FLAGS_INIT", "--specs=nosys.specs", True)

    cmake += ""
    print("# Saving CMake script with toolchain configuration...")
    cmake.save(toolchain_file_path)
    del cmake
    # endregion Toolchain file for CMake cross-compiling

    print()
    print("When invoking CMake, add the following parameter:")
    print("    -DCMAKE_TOOLCHAIN_FILE={}".format(toolchain_file_path))
    print("or")
    print("    -DCMAKE_TOOLCHAIN_FILE={}".format(toolchain_file_path.name))
    print()


def generate_cmake_for_makefile(makefile_path: Path, print_ignored: bool = True) -> bool:
    with open(makefile_path, 'r') as f:
        makefile = f.read()

    # Performance improvement.
    # PROJECT_NAME is required variable in Makefiles of interest and this is much faster than parsing with pymake.
    if "PROJECT_NAME" not in makefile:
        return False

    variables = pymake.parser.parse_variables(makefile_path)

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
        name = statement.name
        if name in variable_names:
            statements[name] = statement

    # This Makefile is not relevant if it does not contain certain required variables.
    if any((name not in statements) for name in ("PROJECT_NAME", "SRC_FILES", "INC_FOLDERS", "CFLAGS", "LDFLAGS")):
        if print_ignored:
            print("Ignoring '{}'".format(makefile_path))
        else:
            print(".", end="", flush=True)
        return False
    print("###############################")
    print("Processing '{}'".format(makefile_path))
    print()
    print(variables)
    print("-------------------------------")

    cmake = CMake()
    cmake.set("PROJECT_NAME", statements["PROJECT_NAME"].value)
    cmake += ""
    cmake.set("TARGETS", statements["TARGETS"].value)
    cmake += ""
    cmake.set("SDK_ROOT", statements["SDK_ROOT"].value)
    cmake.set("PROJ_DIR", statements["PROJ_DIR"].value)
    cmake += ""
    cmake += "# Source files common to all targets"
    cmake.set("SRC_FILES", statements["SRC_FILES"].value)
    cmake += ""
    cmake += "# Include folders common to all targets"
    cmake.set("INC_FOLDERS", statements["INC_FOLDERS"].value)
    cmake += ""
    cmake += "# Libraries common to all targets"
    cmake.set("LIB_FILES", statements["LIB_FILES"].value)
    cmake += ""
    cmake += "# Optimization flags"
    cmake.set("OPT", statements["OPT"].value)
    cmake += "# Uncomment the line below to enable link time optimization"
    cmake += "# OPT += -flto"
    cmake += ""
    cmake += ""
    cmake += "# C flags common to all targets"
    cmake.set("CFLAGS", statements["CFLAGS"].value)
    cmake += ""
    cmake += "# C++ flags common to all targets"
    cmake.set("CXXFLAGS", statements["CXXFLAGS"].value)
    cmake += ""
    cmake += "# Assembler flags common to all targets"
    cmake.set("ASMFLAGS", statements["ASMFLAGS"].value)
    cmake += ""
    cmake += "# Linker flags"
    cmake.set("LDFLAGS", statements["LDFLAGS"].value)
    cmake += ""
    cmake += ""
    cmake += "project(${PROJECT_NAME})"
    cmake += ""
    cmake += 'list(APPEND CFLAGS "-undef" "-D__GNUC__")'
    cmake += "list(FILTER CFLAGS EXCLUDE REGEX mcpu)"
    cmake += 'string(REPLACE ";" " " CFLAGS "${CFLAGS}")'
    cmake += "set(CMAKE_C_FLAGS ${CFLAGS})"
    cmake += ""
    cmake += "include_directories(${INC_FOLDERS})"
    cmake += ""
    cmake += "add_executable(${PROJECT_NAME} ${SRC_FILES})"
    cmake += ""

    # Replace string expansions from Make to CMake syntax.
    # s: str = f.getvalue()
    # for name in variable_names:
    #     # When using str.format, "{{" and "}}" is used to print "{" and "}", that is why there are {{+{ below.
    #     s = s.replace("$({})".format(name), "${{{}}}".format(name))
    #
    # with open(makefile_path.parent.joinpath("CMakeLists.txt"), 'w') as cmake_f:
    #     cmake_f.write(s)

    return True


def generate_cmake_for_examples(sdk_root: Path) -> int:
    cmake = CMake()
    cmake += "# Configure toolchain"
    cmake += "include(arm-gcc-toolchain.cmake)"
    cmake += ""
    # Go trough all makefiles in all of the SDK subdirectories.
    for dir_path, dir_names, filenames in os.walk(str(sdk_root)):
        dir_path = Path(dir_path)
        for filename in filenames:
            if filename == "Makefile":
                if generate_cmake_for_makefile(dir_path.joinpath(filename)):
                    cmake += "#add_subdirectory(./{})".format(dir_path.relative_to(sdk_root).as_posix())
    cmake += ""

    # cmake.save(sdk_root.joinpath("CMakeLists.txt"))

    return 0


def discover_include_directories(sdk_root: Path) -> int:
    dirs = []

    for dir_path, dir_names, filenames in os.walk(str(sdk_root)):
        dir_path = Path(dir_path)
        sdk_subdir = dir_path.relative_to(sdk_root)

        # Exclude examples directory
        if any(str(sdk_subdir).startswith(x) for x in (".git", ".idea", "examples", "cmake-build-debug")):
            continue

        for filename in filenames:
            if os.path.splitext(filename)[1] in (".h", ".hpp"):
                dirs.append(dir_path)
                break

    dirs.sort()
    print("Subdirectories which contains any .h or .hpp files, relative to '{}':".format(str(sdk_root)))
    for d in dirs:
        print(str(d.relative_to(sdk_root).as_posix()))
    print("Done.")

    return 0


def discover_source_files(sdk_root: Path) -> int:
    files = []

    for dir_path, dir_names, filenames in os.walk(str(sdk_root)):
        dir_path = Path(dir_path)
        sdk_subdir = dir_path.relative_to(sdk_root)

        # Exclude examples directory
        if any(str(sdk_subdir).startswith(x) for x in (".git", ".idea", "examples", "cmake-build-debug")):
            continue

        for filename in filenames:
            if os.path.splitext(filename)[1] in (".c", ".cpp", ".s", ".S"):
                files.append(dir_path.joinpath(filename))

    files.sort()
    print("Source files, relative to '{}':".format(str(sdk_root)))
    for f in files:
        print('"${{NRF5_SDK_ROOT}}/{}"'.format(str(f.relative_to(sdk_root).as_posix())))
    print("Done.")

    return 0


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
    parser.add_argument("command", nargs='?', default=False,
                        help="'includes' to generate list of directories which contain header files or "
                             "'sources' to generate list of source files.")
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

    args = parser.parse_args()
    args = vars(args)

    # endregion Parse arguments

    # region Check parameters

    # Provided arguments have higher priority - however keep defaults if argument is not provided.
    def join_arguments(var_name: str, default: Optional[Union[str, Path]] = None) -> Optional[Union[str, Path]]:
        # Argument value will always be a list because of nargs='+'.
        if not isinstance(args[var_name], list):
            # This argument was not provided.
            return default
        # Arguments are cut at spaces (" ") when provided via command line and then put in list.
        # If argument was enclosed in quotes, they are also captured.
        return " ".join(args[var_name]).strip("\"'") or None

    sdk_root = join_arguments("NRF5_SDK_ROOT", sdk_root)
    gcc = join_arguments("GCC", gcc)
    nrfjprog = join_arguments("NRFJPROG", nrfjprog)
    sdk_config = join_arguments("SDK_CONFIG")

    examples: bool = args["EXAMPLES"]

    # sdk_root shall be provided (handled by argparse).
    sdk_root: Path = Path(sdk_root)
    if not (sdk_root.is_dir() and sdk_root.joinpath("components").is_dir() and sdk_root.joinpath("external").is_dir()):
        print("NRF5_SDK_ROOT shall be directory containing at least 'components' and 'external' subdirectories.")
        return -1

    # gcc shall be provided (handled by argparse).
    gcc: Path = Path(gcc)
    if not os.access(str(gcc), os.X_OK):
        print("GCC shall be valid path to the GNU ARM Embedded Toolchain 'gcc' executable "
              "(usually [arm-none-eabi-]gcc[.exe]).")
        return -2

    # nrfjprog shall be valid if provided.
    if nrfjprog:
        nrfjprog = Path(nrfjprog)
        # noinspection PyTypeChecker
        if not os.access(nrfjprog, os.X_OK):
            print("Path to the nrfjprog executable ('{}') is invalid.".format(nrfjprog))
            return -3

    # sdk_config shall be header file if provided.
    if sdk_config and not os.access(sdk_config, os.R_OK):
        print("Path to the sdk_config.h file ('{}') is invalid.".format(sdk_config))
        return -4

    includes = (args["command"] == "includes")
    sources = (args["command"] == "sources")

    # endregion Check parameters

    if includes:
        return discover_include_directories(sdk_root)

    if sources:
        return discover_source_files(sdk_root)

    generate_common_cmakes(gcc, sdk_root, nrfjprog)

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
