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
from typing import Optional, Dict, Union

import pymake.pymake.parser
import pymake.pymake.parserdata
from pymake import pymake

__author__ = "Bojan Potočnik"


def cmake_set_variable(name: str, value: Union[Dict, str]) -> str:
    if isinstance(value, dict):
        value = value[name]
    return "set({} {})".format(name, value)


def write_line(f: io.StringIO, line: Optional[str] = None):
    f.write((line or "") + "\n")


def generate_cmake_for_makefile(makefile_path: str, print_ignored: bool = True) -> None:
    with open(makefile_path, 'r') as f:
        makefile = f.read()

    # Performance improvement.
    # PROJECT_NAME is required variable in Makefiles of interest and this is much faster than parsing with pymake.
    if "PROJECT_NAME" not in makefile:
        return

    # if "gzll_nrf52_sd_resources_gcc" not in makefile:
    #    # This is to process only few makefiles and then stop.
    #    return

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
        return
    print("\nProcessing '{}'".format(makefile_path))

    f = io.StringIO()
    write_line(f, "# CMake file made with Nordic nRF5 SDK CMake Generator")
    write_line(f, "# https://github.com/bojanpotocnik/nrf5-sdk-cmake-generator.git")
    write_line(f, "cmake_minimum_required(VERSION 2.4.0)")
    write_line(f)
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
    write_line(f)

    s = ""
    s += '\n'
    s += 'project(${PROJECT_NAME})\n'
    s += 'cmake_minimum_required(VERSION 2.4.0)\n'
    s += 'project(${PROJECT_NAME})\n'
    s += 'list(APPEND CFLAGS "-undef" "-D__GNUC__")\n'
    s += 'list(FILTER CFLAGS EXCLUDE REGEX mcpu)\n'
    s += 'string(REPLACE ";" " " CFLAGS "${CFLAGS}")\n'
    s += 'set(CMAKE_C_FLAGS ${CFLAGS})\n'
    s += 'include_directories(${INC_FOLDERS})\n'
    s += 'add_executable(${PROJECT_NAME} ${SRC_FILES})\n'

    s: str = f.getvalue()
    # Replace string expansions
    s = s.replace("$(SDK_ROOT)", "${SDK_ROOT}")
    s = s.replace("$(PROJ_DIR)", "${PROJ_DIR}")
    s = s.replace("$(OPT)", "${OPT}")
    s = s.replace("$(TEMPLATE_PATH)", "${TEMPLATE_PATH}")
    s = s.replace("$(LINKER_SCRIPT)", "${LINKER_SCRIPT}")

    # print(s)

    return

    print(makefile_statements)

    s = ""
    s += '\n'
    s += 'project(${PROJECT_NAME})\n'
    s += 'cmake_minimum_required(VERSION 2.4.0)\n'
    s += 'project(${PROJECT_NAME})\n'
    s += 'list(APPEND CFLAGS "-undef" "-D__GNUC__")\n'
    s += 'list(FILTER CFLAGS EXCLUDE REGEX mcpu)\n'
    s += 'string(REPLACE ";" " " CFLAGS "${CFLAGS}")\n'
    s += 'set(CMAKE_C_FLAGS ${CFLAGS})\n'
    s += 'include_directories(${INC_FOLDERS})\n'
    s += 'add_executable(${PROJECT_NAME} ${SRC_FILES})\n'


def generate_cmake_for_examples(sdk_root: str) -> int:
    print(sdk_root)
    for dir_path, dir_names, filenames in os.walk(sdk_root):
        for filename in filenames:
            if filename == "Makefile":
                generate_cmake_for_makefile(os.path.join(dir_path, filename))

    """
    tmp_makefile="/tmp/CMakeLists-generator.mk"

    \cat << 'EOF' > ${tmp_makefile}
    include Makefile
    generate:
    	$(foreach var, PROJECT_NAME SDK_ROOT PROJ_DIR SRC_FILES INC_FOLDERS CFLAGS CXXFLAGS, \
    		echo "set($(var) $($(var)))" ; \
    		echo ; \
    	)
    	@echo 'cmake_minimum_required(VERSION 2.4.0)'
    	@echo 'project($$$ {PROJECT_NAME})'
    	@echo 'list(APPEND CFLAGS "-undef" "-D__GNUC__")'
    	@echo 'list(FILTER CFLAGS EXCLUDE REGEX mcpu)'
    	@echo 'string(REPLACE ";" " " CFLAGS "$$$ {CFLAGS}")'
    	@echo 'set(CMAKE_C_FLAGS $$$ {CFLAGS})'
    	@echo 'include_directories($$$ {INC_FOLDERS})'
    	@echo 'add_executable($$$ {PROJECT_NAME} $$$ {SRC_FILES})'
    EOF
    \echo "cmake_minimum_required(VERSION 2.8.9)" > CMakeLists.txt
    for makefile in `\find ./examples -name Makefile` ; do
        dir=`\dirname ${makefile}`
        \echo "Creating CMakeLists.txt for ${makefile}"
        \pushd ${dir} > /dev/null
        \make -s -f ${tmp_makefile} generate > CMakeLists.txt
        \popd > /dev/null
        \echo "#add_subdirectory(${dir})" >> CMakeLists.txt
    done
    \rm ${tmp_makefile}
    echo '************************************'
    echo 'Enjoy using CLION with the NRF5-SDK!'
    echo '************************************'
    """

    return 0


def main() -> int:
    import argparse
    import distutils.spawn
    from pathlib import Path

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
                             "also be used to find other tools (g++, objcopy, objdump, size)."
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
    args = parser.parse_args(r'--sdk G:\Git\Dia-Vit\FW\nRF5_SDK -e'.split(" "))
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
    sdk_root = Path(sdk_root)
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
    objcopy = gcc_root.joinpath(gcc_prefix + "objcopy" + gcc_extension)
    objdump = gcc_root.joinpath(gcc_prefix + "objdump" + gcc_extension)
    size = gcc_root.joinpath(gcc_prefix + "size" + gcc_extension)

    if not all(os.access(str(exe), os.X_OK) for exe in (gcc, gpp, objcopy, objdump, size)):
        print("GCC shall be valid path to the GNU ARM Embedded Toolchain 'gcc' executable, next to which "
              "shall also be located g++, objcopy, objdump and size tools with the same prefix and extension.")
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
