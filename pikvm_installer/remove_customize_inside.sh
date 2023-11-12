relative_source ../shell_log.sh

remove_customize_inside() {
    log_i "Removing customization inside from the target rootfs..."
    sudo rm -rf ${dir_pacstrap_rootfs}/root/pikvm_installer
}