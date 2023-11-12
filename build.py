import os
from os_builder.scripts.out.py_modules.tools import Logger, run_cmd_with_exit

logger = Logger(name="log")

path_base = os.path.dirname(os.path.abspath(__file__))
path_os_builder = os.path.join(path_base, "os_builder")

logger.info("base_path: " + path_base)


def prepare_config():
    logger.info("Preparing config...")
    run_cmd_with_exit("cp ./config.ini os_builder/config.ini")


def restore_os_builder():
    os.chdir(path_os_builder)
    run_cmd_with_exit("git checkout .")
    run_cmd_with_exit("git clean -df")
    os.chdir(path_base)


def copy_pikvm_installer():
    run_cmd_with_exit("cp -r pikvm_installer os_builder/scripts/in")
    run_cmd_with_exit(
        "mv os_builder/scripts/in/pikvm_installer/customize_inside.sh os_builder/scripts/in/configure_rootfs/customize_inside.sh"
    )
    run_cmd_with_exit(
        "mv os_builder/scripts/in/pikvm_installer/prepare_customize_inside.sh os_builder/scripts/in/configure_rootfs/prepare_customize_inside.sh"
    )
    run_cmd_with_exit(
        "mv os_builder/scripts/in/pikvm_installer/remove_customize_inside.sh os_builder/scripts/in/configure_rootfs/remove_customize_inside.sh"
    )


__main__ = "__main__"
try:
    run_cmd_with_exit("rm -rf os_builder/releases")
    prepare_config()
    copy_pikvm_installer()
    os.chdir(path_os_builder)
    run_cmd_with_exit("python3 build.py")
    os.chdir(path_base)
except Exception as e:
    logger.error("Prepare config error. " + e.__str__())
finally:
    os.chdir(path_base)
    restore_os_builder()
    pass
