Building from source
====================

Install vineyard
----------------

Vineyard is distributed as a `python package <https://pypi.org/project/vineyard/>`_
and can be easily installed with :code:`pip`:

.. code:: shell

    pip3 install vineyard

Install etcd
------------

Vineyard is based on `etcd <https://etcd.io/>`_, please refer the `doc <https://etcd.io/docs/latest/install/>`_ to install it.

Install from source
-------------------

Vineyard is open source on Github: `https://github.com/v6d-io/v6d <https://github.com/v6d-io/v6d>`_.
You can obtain the source code using ``git``:

.. code:: console

    git clone https://github.com/v6d-io/v6d
    cd v6d
    git submodule update --init

Prepare dependencies
^^^^^^^^^^^^^^^^^^^^

Vineyard can be built and deployed on common Unix-like systems. Vineyard has been
fully tests with C++ compilers that supports C++ 14.

Dependencies
~~~~~~~~~~~~

Vineyard requires the following software as dependencies to build and run:

+ apache-arrow >= 3.0.0
+ gflags
+ glog
+ boost
+ mpi, for the graph data structure module

If you want to build the vineyard server, the following additional libraries are needed:

+ protobuf
+ grpc

And the following python packages are required:

+ libclang

  Can be installed using pip

  .. code:: shell

      pip3 install libclang

Install on Ubuntu (or Debian)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Vineyard has been fully tested on Ubuntu 20.04. The dependencies can be installed by

.. code:: shell

    apt-get install -y ca-certificates \
                       cmake \
                       doxygen \
                       libboost-all-dev \
                       libcurl4-openssl-dev \
                       libgflags-dev \
                       libgoogle-glog-dev \
                       libgrpc-dev \
                       libgrpc++-dev \
                       libmpich-dev \
                       libprotobuf-dev \
                       libssl-dev \
                       libunwind-dev \
                       libz-dev \
                       protobuf-compiler-grpc \
                       python3-pip \
                       wget

Then install the apache-arrow (see also `https://arrow.apache.org/install <https://arrow.apache.org/install/>`_):

.. code:: shell

    wget https://apache.jfrog.io/artifactory/arrow/$(lsb_release --id --short | tr 'A-Z' 'a-z')/apache-arrow-apt-source-latest-$(lsb_release --codename --short).deb \
        -O /tmp/apache-arrow-apt-source-latest-$(lsb_release --codename --short).deb
    apt install -y -V /tmp/apache-arrow-apt-source-latest-$(lsb_release --codename --short).deb
    apt update -y
    apt install -y libarrow-dev

Dependencies on MacOS
~~~~~~~~~~~~~~~~~~~~~

Vineyard has been tested on MacOS as well, the dependencies can be installed using :code:`brew`:

.. code:: shell

    brew install apache-arrow boost gflags glog grpc protobuf llvm mpich openssl zlib autoconf

Building vineyard
^^^^^^^^^^^^^^^^^

After the required dependencies are installed, you do an out-of-source build using **CMake**:

.. tip::

    We recommend to use the brew installed LLVM as the compiler for building vineyard on MacOS,
    which can be accomplished by setting the environment variable :code:`CC` and :code:`CXX`:

    .. code::

        export CC=$(brew --prefix llvm)/bin/clang
        export CXX=$(brew --prefix llvm)/bin/clang++

.. code:: shell

    mkdir build
    cd build
    cmake ..
    make -j$(nproc)
    sudo make install  # optionally

You will see vineyard server binary under the ``bin`` directory, and static or shared linked
libraries will be placed under the ``lib-shared`` folder.

Building python wheels
^^^^^^^^^^^^^^^^^^^^^^

After building the vineyard library successfully, you can package an install wheel distribution by

.. code:: shell

    python3 setup.py bdist_wheel

Install vineyardctl
-------------------

Vineyardctl is available on the Github release page, you can download the binary as follows:

.. code:: shell

    export LATEST_TAG=$(curl -s "https://api.github.com/repos/v6d-io/v6d/tags" | jq -r '.[0].name')
    export OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    export ARCH=${$(uname -m)/x86_64/amd64}
    curl -Lo vineyardctl https://github.com/v6d-io/v6d/releases/download/$LATEST_TAG/vineyardctl-$LATEST_TAG-$OS-$ARCH
    chmod +x vineyardctl
    sudo mv vineyardctl /usr/local/bin/


Building the documentation
--------------------------

Vineyard documentation is organized and generated by sphinx. There are other packages that
help us build the documentation, which can be easily installed using ``pip``:

.. code:: shell

    pip3 install -r requirements.txt -r requirements-dev.txt

Once installed, you could go to the `docs/` directory and build the documentation by

.. code:: shell

    cd docs/  # skip if you are already there
    make html

Building on various platforms
-----------------------------

Vineyard is continuously tested on various platforms and you may find building and installation steps
from our CI:

- `Ubuntu <https://github.com/v6d-io/v6d/blob/main/.github/workflows/build-compatibility.yml>`_
- `MacOS <https://github.com/v6d-io/v6d/blob/main/.github/workflows/build-compatibility.yml>`_
- `CentOS <https://github.com/v6d-io/v6d/blob/main/.github/workflows/build-centos-latest.yaml>`_
- `Arch Linux <https://github.com/v6d-io/v6d/blob/main/.github/workflows/build-archlinux-latest.yml>`_
