#
# To prepare u-boot script, run:
# mkimage -A arm64 -T script -O linux -d h618-boot.txt h618-boot.scr
#

part uuid ${devtype} ${devnum}:3 uuid # 将设备的第二个分区的 UUID 存储在名为 "uuid" 的变量中

setenv bootargs root=PARTUUID=${uuid} rw rootwait earlycon console=ttyS0,115200n8 logo.nologo vt.cur_default=1 deferred_probe_timeout=0
# root=PARTUUID=${uuid}: 这是 bootargs 的一个参数，它定义了根文件系统的位置。
# root 后跟等号指定了根文件系统的位置，其中 PARTUUID 表示使用分区的 UUID 来标识根文件系统的位置。
# ${uuid} 是之前通过 part uuid 命令获取的第二个分区的 UUID。这样，
# 内核将使用这个 UUID 来识别并挂载正确的分区作为根文件系统。
# rw: 这个参数表示根文件系统应该以可读写（read-write）模式挂载。
# rootwait: 这个参数表示内核应该等待根文件系统就绪，以确保根文件系统已经准备好挂载。
# earlycon console=ttyS0,115200n8: 这一部分配置了串口终端，
# 指定了串口设备 ttyS0，波特率为 115200，以及数据位数 8。
# logo.nologo: 这个参数通常是用来禁用 Linux 内核启动时的 Logo 显示。
# vt.cur_default=1: 这个参数配置了虚拟终端（Virtual Terminal）的默认选项，设置为 1。
# deferred_probe_timeout=0: 这个参数通常用于控制设备的延迟探测时间，将其设置为 0 表示没有延迟探测。

setenv fdtfile dtbs/linux-aarch64-orangepi-zero3/allwinner/sun50i-h616-orangepi-zero3.dtb
setenv userfdtfile h618_dtb

if load ${devtype} ${devnum}:${bootpart} ${kernel_addr_r} /vmlinuz-linux-aarch64-orangepi-zero3; then
  if load ${devtype} ${devnum}:${bootpart} ${fdt_addr_r} /${userfdtfile}; then
    fdt addr ${fdt_addr_r}
    fdt resize
    if load ${devtype} ${devnum}:${bootpart} ${ramdisk_addr_r} /initramfs-linux-aarch64-orangepi-zero3-fallback.img; then
      booti ${kernel_addr_r} ${ramdisk_addr_r}:${filesize} ${fdt_addr_r}
    else
      booti ${kernel_addr_r} - ${fdt_addr_r}
    fi;
  else
    if load ${devtype} ${devnum}:${bootpart} ${fdt_addr_r} /${fdtfile}; then
      fdt addr ${fdt_addr_r}
      fdt resize
      if load ${devtype} ${devnum}:${bootpart} ${ramdisk_addr_r} /initramfs-linux-aarch64-orangepi-zero3-fallback.img; then
        booti ${kernel_addr_r} ${ramdisk_addr_r}:${filesize} ${fdt_addr_r}
      else
        booti ${kernel_addr_r} - ${fdt_addr_r}
      fi;
    else
      if load ${devtype} ${devnum}:${bootpart} ${ramdisk_addr_r} /initramfs-linux-aarch64-orangepi-zero3-fallback.img; then
        booti ${kernel_addr_r} ${ramdisk_addr_r}:${filesize} ${fdtcontroladdr}
      else
        booti ${kernel_addr_r} - ${fdtcontroladdr}
      fi;
    fi;
  fi;
fi
