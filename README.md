# kboot

Kboot is a script that presents a menu of available kernels (from the grub configuration), prompts for a kernel from the list and will one-time-boot the selected kernel. This came from my frustration of waiting for incredibly long POSTs to complete so that the grub menu would display and I could select a kernel to boot. I've since added kexec functionality to totally bypass the wait for slow BIOS code.
