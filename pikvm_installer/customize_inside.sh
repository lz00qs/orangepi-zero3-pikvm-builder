customize_inside() {
    echo " => Customize inside the target root"
    echo "blank"
    pushd "/root"
    ls -l
    path=$(pwd)
    echo "customize_inside path: ${path}"
    pushd "/root/pikvm_installer"
    chmod +x install_pikvm.sh
    ./install_pikvm.sh
    popd > /dev/null
    popd > /dev/null
    echo " => Customize inside the target root done"
}
