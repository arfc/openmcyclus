FROM cyclus/cycamore:latest

COPY . /openmcyclus
RUN conda install pyqt -y && \
    conda install -c bashtage -y && \
    conda install matplotlib scipy numpy -y && \
    conda update --all -y && \
    pip install pmdarima && \
    pip install -U pytest nose && \
    pip uninstall h5py && \
    pip install --no-cache-dir h5py && \
    sudo apt-get update && \
    sudo apt-get install libhdf5-dev && \
    sudo apt-get update && \
    sudo apt-get install libhdf5-serial-dev && \
    python install.py
