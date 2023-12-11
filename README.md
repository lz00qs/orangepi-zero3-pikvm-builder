# orangepi-zero3-pikvm-builder
## Usage

This builder has only been verified on debian > 10 and ubuntu > 20.04.


Firstly, install the required build package in your system:
```bash
sudo apt install \
   arch-install-scripts \
   bc \
   bison \
   distcc \
   flex \
   libarchive-tools \
   qemu-user-static \
   libssl-dev \
   qemu-user-static \
   u-boot-tools \
   python3 \
   python3-pip \
   pigz
```


Secondly, clone this repo with `--recursive` option:
```bash
git clone --recursive https://github.com/lz00qs/orangepi-zero3-archlinux-builder.git
```


Finally, build:
```bash
python3 build.py
```

> You can change some configurations in `config.ini`.

You can use clean.py to clean all built files:
```bash
python3 clean.py
```

## Contributions

@lz00qs

## License

GPL V3.0
