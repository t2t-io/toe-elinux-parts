dependencies:
	# The debian packages to be installed via `apt-get install`.
	# For example, when you add one line `* <[socat screen vim]>`
	# under `debian` section, the apply_parts subcommand shall perform
	# `apt-get install -y socat screen vim` in the context of 
	# chroot with qemu.
	#
	debian:
		# Utilities
		# 
		* []

	# The python2 packages to be installed via `pip install`.
	# For example, when you specify `python2: <[httpie colorama]>` here,
	# the apply_parts subcommand shall perform `pip install httpie colorama`
	# in the context of chroot with qemu.
	#
	python2: []

	# The python3 packages to be installed via `pip3 install`
	# For example, when you specify `python3: <[httpie colorama]>` here,
	# the apply_parts subcommand shall perform `pip3 install httpie colorama`
	# in the context of chroot with qemu.
	#
	python3: []
