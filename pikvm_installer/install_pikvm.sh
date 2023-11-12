#/bin/bash -e

PIKVM_REPO_KEY=912C773ABBD1B584
PIKVM_REPO_URL=https://files.pikvm.org/repos/arch/
BOARD=rpi4
PLATFORM=v2-hdmiusb

install_basic_pkg() {
    # pacman-key --init
    # pacman-key --populate archlinuxarm
    # pacman --noconfirm --ask=4 -Syy
    echo "Server = https://mirrors.ustc.edu.cn/archlinuxarm/\$arch/\$repo" >/etc/pacman.d/mirrorlist &&
        pacman-key --init &&
        pacman-key --populate archlinuxarm
    pacman --needed --noconfirm --ask=4 -S \
        glibc \
        openssl \
        openssl-1.1
    pacman --needed --noconfirm --ask=4 -S pacman
    pacman-db-upgrade
    pacman-key --init
    pacman --needed --noconfirm --ask=4 -S \
        base \
        base-devel \
        vim \
        colordiff \
        tree \
        wget \
        unzip \
        unrar \
        htop \
        nmap \
        ethtool \
        iftop \
        iotop \
        dysk \
        strace \
        usbutils \
        pciutils \
        lsof \
        git \
        jshon \
        rng-tools \
        bc \
        ccache \
        screen \
        dosfstools
    rm -rf /var/cache/pacman/pkg/*

    # https://github.com/pikvm/pikvm/issues/190
    systemctl disable haveged || true
    echo 'RNGD_OPTS="-o /dev/random -r /dev/hwrng -x jitter -x pkcs11 -x rtlsdr"' >/etc/conf.d/rngd &&
        systemctl enable rngd

    sed -i -e "s/^#MAKEFLAGS=.*/MAKEFLAGS=-j5/g" /etc/makepkg.conf
    sed -i -e "s/ \!ccache / ccache /g" /etc/makepkg.conf
    export PATH="/usr/lib/ccache/bin/:${PATH}"

    sed -i -e '/\<pam_systemd\.so\>/ s/^#*/#/' /etc/pam.d/system-login &&
        sed -i -e '/\<pam_systemd_home\.so\>/ s/^#*/#/' /etc/pam.d/system-auth

    echo "DNSSEC=no" >>/etc/systemd/resolved.conf &&
        systemctl enable systemd-resolved

    cp e2fsck.conf /etc/

    cp gitconfig /etc/skel/.gitconfig
    cp gitconfig /root/.gitconfig
    cp gitconfig /home/alarm/.gitconfig

    mkdir /tmp/linux-profile &&
        git clone https://github.com/mdevaev/linux-profile.git /tmp/linux-profile --depth=1 &&
        cp -a /tmp/linux-profile/{.bash_profile,.bashrc,.vimrc,.vimpagerrc,.vim} /etc/skel &&
        cp -a /tmp/linux-profile/{.bash_profile,.bashrc,.vimrc,.vimpagerrc,.vim} /root &&
        cp -a /tmp/linux-profile/{.bash_profile,.bashrc,.vimrc,.vimpagerrc,.vim} /home/alarm &&
        chown -R alarm:alarm /home/alarm/{.bash_profile,.bashrc,.vimrc,.vimpagerrc,.vim,.gitconfig} &&
        rm -rf /tmp/linux-profile

    cp pistat /usr/local/bin/
    cp pkg-install /usr/local/bin/
}

install_pikvm_repo() {
    (
        mkdir -p /etc/gnupg &&
            echo standard-resolver >>/etc/gnupg/dirmngr.conf &&
            (
                pacman-key --keyserver hkps://keyserver.ubuntu.com:443 -r $PIKVM_REPO_KEY ||
                    pacman-key --keyserver hkps://keys.gnupg.net:443 -r $PIKVM_REPO_KEY ||
                    pacman-key --keyserver hkps://pgp.mit.edu:443 -r $PIKVM_REPO_KEY
            )
    ) &&
        pacman-key --lsign-key $PIKVM_REPO_KEY &&
        echo -e "\n[pikvm]" >>/etc/pacman.conf &&
        echo "Include = /etc/pacman.d/pikvm" >>/etc/pacman.conf &&
        echo "SigLevel = Required DatabaseOptional" >>/etc/pacman.conf &&
        echo "Server = $PIKVM_REPO_URL/$BOARD" >/etc/pacman.d/pikvm
}

install_pikvm_pkg() {

}

install_basic_pkg
install_pikvm_repo
