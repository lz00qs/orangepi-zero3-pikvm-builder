import configparser
import os
import subprocess
import sys
import uuid
from .tools import Logger, run_cmd_with_exit

logger = Logger(name="log")

release_prefix = ""
file_name_img = ""
img_size = ""
path_releases = ""
path_releases_img = ""
table_type = ""
boot_part_start = ""
boot_part_end = ""
fstab_templete = ""
rootfs_part_end = ""
pimsd_part_end = ""


def subtract_megabytes(str1, str2):
    megabytes1 = int(str1.rstrip("M"))
    megabytes2 = int(str2.rstrip("M"))
    result_megabytes = megabytes1 - megabytes2
    result_str = f"{result_megabytes}M"
    return result_str


def add_megabytes(str1, str2):
    megabytes1 = int(str1.rstrip("M"))
    megabytes2 = int(str2.rstrip("M"))
    result_megabytes = megabytes1 + megabytes2
    result_str = f"{result_megabytes}M"
    return result_str


def load_config():
    logger.info("Loading img config...")
    config = configparser.ConfigParser()
    config.read("config.ini.split")
    global release_prefix
    release_prefix = os.environ["RELEASE_PREFIX"]
    global img_size
    img_size = config.get("ImgConfig", "img_size")
    global file_name_img
    file_name_img = f"{release_prefix}.img"
    global path_releases_img
    global path_releases
    path_releases = os.environ["PATH_RELEASES"]
    path_releases_img = os.path.join(path_releases, file_name_img)
    global table_type
    table_type = config.get("ImgConfig", "table_type")
    global boot_part_start
    boot_part_start = config.get("ImgConfig", "boot_part_start")
    global boot_part_end
    boot_part_end = config.get("ImgConfig", "boot_part_end")
    global fstab_templete
    fstab_templete = config.get("FstabConfig", "fstab_templete")

    pimsd_part_size = config.get("ImgConfig", "pimsd_part_size")
    pipst_part_size = config.get("ImgConfig", "pipst_part_size")
    global pimsd_part_end
    pimsd_part_end = subtract_megabytes(img_size, pipst_part_size)
    global rootfs_part_end
    rootfs_part_end = subtract_megabytes(pimsd_part_end, pimsd_part_size)
    


def create_blank_disk():
    logger.info("Creating blank disk...")
    try:
        run_cmd_with_exit(f"sudo rm -f {path_releases_img}")
        img_size_num = int(img_size[:-1])
        run_cmd_with_exit(
            f"dd if=/dev/zero of={path_releases_img} bs=1M count={img_size_num}"
        )
    except Exception as e:
        logger.error("Create blank disk error. " + e.__str__())
        sys.exit(1)


def create_partition():
    logger.info("Creating disk partition...")
    if table_type == "msdos":
        run_cmd_with_exit(
            f"parted {path_releases_img} mklabel msdos "
            + f"mkpart primary fat32 {boot_part_start}iB {boot_part_end}iB "
            + "set 1 boot on "
            + f"mkpart primary ext4 {boot_part_end}iB {rootfs_part_end}iB "
            + f"mkpart primary ext4 {rootfs_part_end}iB {pimsd_part_end}iB "
            + f"mkpart primary ext4 {pimsd_part_end}iB 100%"
        )
    elif table_type == "gpt":
        run_cmd_with_exit(
            f"parted {path_releases_img} mklabel  "
            + f"mkpart ArchBoot fat32 {boot_part_start}iB {boot_part_end}iB "
            + f"mkpart ArchRoot ext4 {boot_part_end}iB {rootfs_part_end}iB "
            + f"mkpart PIMSD ext4 {rootfs_part_end}iB {pimsd_part_end}iB "
            + f"mkpart PIPST ext4 {pimsd_part_end}iB 100%"
        )
    else:
        logger.error("Unknown table type.")
        sys.exit(1)


loop_device = ""
loop_boot = ""
loop_root = ""
loop_pimsd = ""
loop_pipst = ""

def setup_loop():
    logger.info("Setting up loop device...")
    try:
        global loop_device
        loop_device = (
            subprocess.run(
                f"sudo losetup -fP --show {path_releases_img}",
                shell=True,
                check=True,
                capture_output=True,
            )
            .stdout.decode("utf-8")
            .rstrip("\n")
        )
        logger.info(f"Using loop device {loop_device}")
        global loop_boot
        loop_boot = f"{loop_device}p1"
        global loop_root
        loop_root = f"{loop_device}p2"
        global loop_pimsd
        loop_pimsd = f"{loop_device}p3"
        global loop_pipst
        loop_pipst = f"{loop_device}p4"
    except Exception as e:
        logger.error("Set up loop device error. " + e.__str__())
        sys.exit(1)


uuid_boot_mkfs = ""
uuid_boot_specifier = ""
uuid_root = ""


def generate_uuid():
    logger.info("Generating uuid...")
    global uuid_boot_mkfs
    uuid_boot_mkfs = str(uuid.uuid4())[:8].upper()
    global uuid_boot_specifier
    uuid_boot_specifier = f"{uuid_boot_mkfs[:4]}-{uuid_boot_mkfs[4:]}"
    logger.info(
        f"uuid_mkfs: {uuid_boot_mkfs} | uuid_boot_specifier: {uuid_boot_specifier}"
    )
    global uuid_root
    uuid_root = str(uuid.uuid4())
    logger.info(f"uuid_root: {uuid_root}")


def create_fs():
    logger.info("Creating fs...")
    try:
        logger.info(f"Creating FAT32 FS with UUID {uuid_boot_mkfs} on {loop_boot}")
        run_cmd_with_exit(
            f"sudo mkfs.vfat -n 'ALARMBOOT' -F 32 -i {uuid_boot_mkfs} {loop_boot}"
        )
        logger.info(f"Creating ext4 FS with UUID {uuid_root} on {loop_root}")
        run_cmd_with_exit(
            f"sudo mkfs.ext4 -L 'ALARMROOT' -m 0 -U {uuid_root} {loop_root}"
        )
        logger.info(f"Creating ext4 FS with Label 'PIMSD' on {loop_pimsd}")
        run_cmd_with_exit(f"sudo mkfs.ext4 -L 'PIMSD' -m 0 {loop_pimsd}")
        logger.info(f"Creating ext4 FS with Label 'PIPST' on {loop_pipst}")
        run_cmd_with_exit(f"sudo mkfs.ext4 -L 'PIPST' -m 0 {loop_pipst}")
    except Exception as e:
        logger.error("Create fs error. " + e.__str__())
        sys.exit(1)


path_boot = ""
path_root = ""


def mount_fs():
    try:
        global path_boot
        global path_root
        path_root = (
            subprocess.run(
                f"sudo mktemp -d", shell=True, check=True, capture_output=True
            )
            .stdout.decode("utf-8")
            .rstrip("\n")
        )
        path_boot = os.path.join(path_root, "boot")
        logger.info(f"Mounting {loop_root} to {path_root}")
        run_cmd_with_exit(f"sudo mount -o noatime {loop_root} {path_root}")
        logger.info(f"Mounting {loop_boot} to {path_boot}")
        run_cmd_with_exit(f"sudo mkdir -p {path_boot}")
        run_cmd_with_exit(f"sudo mount -o noatime {loop_boot} {path_boot}")
    except Exception as e:
        logger.error("Mount fs error. " + e.__str__())
        sys.exit(1)


def umount_fs():
    logger.info("Unmounting fs...")
    try:
        run_cmd_with_exit(f"sudo umount {path_boot}")
        run_cmd_with_exit(f"sudo umount {path_root}")
    except Exception as e:
        logger.error("Umount fs error. " + e.__str__())
        sys.exit(1)
    finally:
        try:
            logger.info(f"Removing {path_root}")
            run_cmd_with_exit(f"sudo rm -rf {path_root}")
        except Exception as e:
            logger.error("Remove temp dir error. " + e.__str__())
            sys.exit(1)


def extract_built_rootfs():
    logger.info("Extracting built rootfs...")
    try:
        path_releases_rootfs = os.path.join(
            path_releases, f"{release_prefix}-rootfs.tar.gz"
        )
        run_cmd_with_exit(
            f"sudo bsdtar -C {path_root} --acls --xattrs -xpf {path_releases_rootfs}"
        )
    except Exception as e:
        logger.error("Extract built rootfs error. " + e.__str__())
        sys.exit(1)


def generate_fstab():
    logger.info("Generating fstab...")
    try:
        path_fstab_temp = (
            subprocess.run(f"mktemp", shell=True, check=True, capture_output=True)
            .stdout.decode("utf-8")
            .rstrip("\n")
        )
        fstab_modified = fstab_templete.replace(
            "uuid_boot", uuid_boot_specifier
        ).replace("uuid_root", uuid_root)
        with open(path_fstab_temp, "w") as file:
            file.write(fstab_modified)
        run_cmd_with_exit(
            f"sudo install -DTm 644 {path_fstab_temp} {path_root}/etc/fstab"
        )
        run_cmd_with_exit(f"cat {path_root}/etc/fstab")
        print("\n")
    except Exception as e:
        logger.error("Generate fstab error. " + e.__str__())
        sys.exit(1)


def install_bootloader():
    logger.info("Installing bootloader...")
    path_base = os.environ["PATH_BASE"]
    path_booting = os.path.join(path_base, "booting")
    try:
        for script in os.listdir(path_booting):
            if script.endswith(".sh"):
                script_name = script[:-3]
                if script_name == "boot":
                    script_name = "boot.scr"
                run_cmd_with_exit(
                    f"sudo mkimage -A arm64 -O linux -T script -C none -d {os.path.join(path_booting,script)} {os.path.join(path_boot,script_name)}"
                )
        run_cmd_with_exit(f"ls {path_boot}")
        uboot_name = "u-boot-sunxi-with-spl-opizero3-1gb.bin"
        run_cmd_with_exit(
            f"sudo dd bs=1k seek=8 if={os.path.join(path_booting,uboot_name)} of={loop_device}"
        )
    except Exception as e:
        logger.error("Install bootloader error. " + e.__str__())
        sys.exit(1)


def release_resources():
    logger.info("Releasing resources...")
    if loop_device:
        logger.info("Detaching loop device...")
        run_cmd_with_exit(f"sudo losetup -d {loop_device}")
    if path_root:
        umount_fs()


def create_img():
    logger.info("Creating img...")
    try:
        load_config()
        create_blank_disk()
        create_partition()
        setup_loop()
        generate_uuid()
        create_fs()
        mount_fs()
        extract_built_rootfs()
        generate_fstab()
        install_bootloader()
    except Exception as e:
        logger.error("Create img error. " + e.__str__())
        sys.exit(1)
    finally:
        release_resources()
