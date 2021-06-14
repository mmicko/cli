#
# FPGA - Command Line Interface
#
# Copyright (C) 2021  Miodrag Milanovic <mmicko@gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

from setuptools import setup, find_packages
from fpga import __version__

setup(
	name="fpga",
	version=__version__,
	author="Miodrag Milanovic",
	author_email="mmicko@gmail.com",
	description="FPGA - Command Line Interface",
	license="ISC",
	python_requires=">=3.6",
	install_requires=[
		"setuptools",
		"click>=7",
	],
	packages=find_packages(),
	entry_points={
		"console_scripts": [
			"fpga = fpga.__main__:cli"
		]
	},
)
