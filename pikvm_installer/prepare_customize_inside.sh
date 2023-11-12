relative_source ../shell_log.sh

prepare_customize_inside() {
    log_i "Preparing customization inside for the target rootfs..."
    # /home/alarm/build
    sudo cp -r pikvm_installer "${dir_pacstrap_rootfs}/root/pikvm_installer"
}
