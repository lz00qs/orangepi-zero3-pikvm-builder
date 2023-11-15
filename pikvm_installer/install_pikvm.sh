#/bin/bash -e
source config

install_basic_pkg() {
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

    cp os/e2fsck.conf /etc/

    cp os/gitconfig /etc/skel/.gitconfig
    cp os/gitconfig /root/.gitconfig
    cp os/gitconfig /home/alarm/.gitconfig

    mkdir /tmp/linux-profile &&
        git clone https://github.com/mdevaev/linux-profile.git /tmp/linux-profile --depth=1 &&
        cp -a /tmp/linux-profile/{.bash_profile,.bashrc,.vimrc,.vimpagerrc,.vim} /etc/skel &&
        cp -a /tmp/linux-profile/{.bash_profile,.bashrc,.vimrc,.vimpagerrc,.vim} /root &&
        cp -a /tmp/linux-profile/{.bash_profile,.bashrc,.vimrc,.vimpagerrc,.vim} /home/alarm &&
        chown -R alarm:alarm /home/alarm/{.bash_profile,.bashrc,.vimrc,.vimpagerrc,.vim,.gitconfig} &&
        rm -rf /tmp/linux-profile

    cp os/pistat /usr/local/bin/
    cp os/pkg-install /usr/local/bin/
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
    # storage /boot file to avoid modification by pacman
    boot_backup_temp=$(mktemp -d)
    cp -r /boot/* "$boot_backup_temp"

    pacman --noconfirm --ask=4 -Syu
    # pkg-install --assume-installed tessdata \
    #     kvmd-platform-$PLATFORM-$BOARD \
    #     kvmd-webterm \
    #     kvmd-oled \
    #     kvmd-fan \
    #     tesseract \
    #     tesseract-data-eng \
    #     wiringpi \
    #     pastebinit \
    #     dhclient \
    #     tmate \
    #     vi-vim-symlink \
    #     nano-syntax-highlighting \
    #     hostapd \
    #     edid-decode &&
    #     if [[ $PLATFORM =~ ^v4.*$ ]]; then pkg-install flashrom-pikvm; fi

    pkg-install --assume-installed tessdata \
        kvmd-platform-$PLATFORM-$BOARD \
        kvmd-webterm \
        tesseract \
        tesseract-data-eng \
        wiringpi \
        pastebinit \
        dhclient \
        tmate \
        vi-vim-symlink \
        nano-syntax-highlighting \
        hostapd &&
        if [[ $PLATFORM =~ ^v4.*$ ]]; then pkg-install flashrom-pikvm; fi

    systemctl enable kvmd-bootconfig &&
        systemctl enable kvmd &&
        systemctl enable kvmd-pst &&
        systemctl enable kvmd-nginx &&
        systemctl enable kvmd-webterm &&
        if [[ $PLATFORM =~ ^.*-hdmi$ ]]; then systemctl enable kvmd-tc358743; fi &&
        if [[ $PLATFORM =~ ^v0.*$ ]]; then systemctl mask serial-getty@ttyAMA0.service; fi &&
        if [[ $PLATFORM =~ ^v[234].*$ ]]; then
            systemctl enable kvmd-otg &&
                echo "LABEL=PIMSD /var/lib/kvmd/msd  ext4  $PART_OPTS,X-kvmd.otgmsd-user=kvmd  0 2" >>/etc/fstab \
                ;
        fi &&
        if [[ $BOARD =~ ^rpi4|zero2w$ && $PLATFORM =~ ^v[234].*-hdmi$ ]]; then systemctl enable kvmd-janus; fi &&
        if [[ $BOARD =~ ^rpi3$ && $PLATFORM =~ ^v[1].*-hdmi$ ]]; then systemctl enable kvmd-janus; fi &&
        if [[ $PLATFORM =~ ^v[34].*$ ]]; then systemctl enable kvmd-watchdog; fi &&
        if [[ -n "$OLED" || $PLATFORM =~ ^v4.*$ ]]; then systemctl enable kvmd-oled kvmd-oled-reboot kvmd-oled-shutdown; fi &&
        if [[ -n "$FAN" || $PLATFORM == v4plus-hdmi ]]; then systemctl enable kvmd-fan; fi

    cp pikvm/nanorc /etc/skel/.nanorc
    cp -a /etc/skel/.nanorc /root && cp -a /etc/skel/.nanorc /home/kvmd-webterm && chown kvmd-webterm:kvmd-webterm /home/kvmd-webterm/.nanorc

    cp pikvm/motd /etc/
    cp pikvm/issue /etc/

    # userdel -r -f alarm

    echo "$WEBUI_ADMIN_PASSWD" | kvmd-htpasswd set --read-stdin admin

    sed -i "\$d" /etc/kvmd/ipmipasswd &&
        echo "admin:$IPMI_ADMIN_PASSWD -> admin:$WEBUI_ADMIN_PASSWD" >>/etc/kvmd/ipmipasswd

    rm -f /etc/ssh/ssh_host_* /etc/kvmd/nginx/ssl/* /etc/kvmd/vnc/ssl/*

    rm -rf /boot/*
    cp -r "$boot_backup_temp"/* /boot/
    rm -rf "$boot_backup_temp"

    echo "FIRST_BOOT=1" >/boot/pikvm.txt
}

patch_pikvm() {
    sudo mv pikvm/override.yaml /etc/kvmd/override.yaml
    cat /etc/kvmd/override.yaml
    echo -e "#!/bin/sh\necho "rw"" | sudo tee /usr/local/bin/rw
    echo -e "#!/bin/sh\necho "ro"" | sudo tee /usr/local/bin/ro
    chmod +x /usr/local/bin/rw
    chmod +x /usr/local/bin/ro

    rm /usr/bin/ustreamer* || true
    git clone --depth=1 https://github.com/pikvm/ustreamer
    pushd ustreamer >/dev/null
    make -j$(nproc)
    make install
    ln -sf /usr/local/bin/ustreamer* /usr/bin/
    popd >/dev/null
}

install_basic_pkg
install_pikvm_repo
sed -i 's/Architecture = aarch64/Architecture = auto/g' /etc/pacman.conf
install_pikvm_pkg
patch_pikvm
