"""
Generate CMake for Nordic nRF5 SDK which can then be included in custom projects via:
    `TODO: what command?`

Implementation strongly influenced by https://github.com/Jumperr-labs/nrf5-sdk-clion .

Usage
"""
import enum
import os
import sys
from typing import Iterable, Optional

__author__ = "Bojan Potočnik"


def show_usage_help(error_string: Optional[str] = None) -> None:
    if error_string:
        print()
        print("Error:", error_string)
        print()
    print("Usage:")
    path: str = sys.argv[0]
    if path.count(" "):
        path = '"' + path + '"'
    print("\tpython3 {} \"NRF5_SDK_ROOT\"".format(path))
    print("Arguments (shall be enclosed in \"\" if containing spaces):")
    print("\tNRF5_SDK_ROOT : Root directory of the nRF5 SDK, that is directory\n"
          "\t                containing subdirectories components, examples,\n"
          "\t                external, ...")
    print()


def get_line_starting_with(what: str, lines: Iterable[str], case_insensitive: bool = False) -> Optional[str]:
    if case_insensitive:
        what = what.lower()

    for line in lines:
        if case_insensitive:
            line = line.lower()

        if line.startswith(what):
            return line

    return None


@enum.unique
class State(enum.IntEnum):
    SearchingForName = 0
    NameFound = 1


def get_make_variable_value(variable_name: str, lines: Iterable[str]) -> Optional[str]:
    state = State.SearchingForName
    value = ""

    for line in lines:
        line = line.strip()

        if state == State.SearchingForName:
            if line.startswith(variable_name):
                state = State.NameFound
            if state == State.SearchingForName:
                # Name was not found, continue with the next line.
                continue

        if state == State.NameFound:
            raise NotImplementedError()

            # Append?
            var_name, var_value = line.split("+=", 1)

    line_idx = 0
    while True:
        # Find line starting with this variable name:
        found = False
        for i, line in enumerate(lines[line_idx:]):
            if line.strip().startswith(variable_name):
                line_idx = i
                found = True
                break
        if not found:
            break
        # Parse complete value for this variable:
        for i, line in enumerate(lines[line_idx:]):
            raise NotImplementedError()

        if line_idx is None:
            break
        # Search from this line (inclusive) forward to fetch value

    variable = get_line_starting_with(variable_name, lines)
    if not variable:
        return None
    return variable.split(":=")[1].strip()


def generate_cmake_for_makefile(makefile_path: str) -> None:
    # print(makefile_path)

    with open(makefile_path, 'r') as f:
        lines = f.readlines()

    project_name = get_make_variable_value("PROJECT_NAME", lines)
    if not project_name:
        return None

    targets = get_make_variable_value("TARGETS", lines)
    output_directory = get_make_variable_value("OUTPUT_DIRECTORY", lines)
    sdk_root = get_make_variable_value("SDK_ROOT", lines)
    proj_dir = get_make_variable_value("PROJ_DIR", lines)
    src_files = get_make_variable_value("SRC_FILES", lines)
    inc_folders = get_make_variable_value("INC_FOLDERS", lines)
    lib_files = get_make_variable_value("LIB_FILES", lines)
    opt = get_make_variable_value("OPT", lines)

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


def generate_cmake(sdk_root: str) -> int:
    print(sdk_root)
    for dir_path, dir_names, filenames in os.walk(sdk_root):
        for filename in filenames:
            if filename == "Makefile":
                generate_cmake_for_makefile(os.path.join(dir_path, filename))

    return 0


def main() -> int:
    if len(sys.argv) != 2:
        show_usage_help()
        return 0

    return generate_cmake(sys.argv[1])


if __name__ == "__main__":
    sys.argv.append(r"G:\Git\Dia-Vit\FW\nRF5_SDK")
    ret = main()
    print()
    input("Press any key to continue...")
    exit(ret)

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
