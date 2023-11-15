import os
from os_builder.scripts.out.py_modules.tools import (
    Logger,
    run_cmd_with_exit,
    split_config,
)

logger = Logger(name="log")

path_base = os.path.dirname(os.path.abspath(__file__))
path_os_builder = os.path.join(path_base, "os_builder")

logger.info("base_path: " + path_base)


def prepare_config():
    logger.info("Preparing config...")
    with open("config.ini", "r") as original_config:
        original_config = original_config.read()
        pikvm_config, os_builder_config = split_config(original_config, "PiKVMConfig")
        with open("os_builder/config.ini", "w") as os_builder_config_file:
            os_builder_config_file.write(os_builder_config)
        with open("pikvm_installer/config", "w") as pikvm_config_file:
            pikvm_config_file.write(pikvm_config.replace("[PiKVMConfig]", ""))


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
    run_cmd_with_exit(
        "mv os_builder/scripts/in/pikvm_installer/create_img_func.py os_builder/scripts/out/py_modules/create_img_func.py"
    )
    run_cmd_with_exit(
        "rm -f os_builder/booting/boot.sh && mv os_builder/scripts/in/pikvm_installer/booting/boot.sh os_builder/booting/boot.sh"
    )


__main__ = "__main__"
try:
    run_cmd_with_exit("rm -rf os_builder/releases")
    prepare_config()
    copy_pikvm_installer()
    os.chdir(path_os_builder)
    run_cmd_with_exit("python3 build.py")
    os.chdir(path_base)
    if not os.path.exists("releases"):
        os.mkdir("releases")
    run_cmd_with_exit("cp -r os_builder/releases/* releases")
except Exception as e:
    logger.error("Prepare config error. " + e.__str__())
finally:
    os.chdir(path_base)
    restore_os_builder()
    pass
