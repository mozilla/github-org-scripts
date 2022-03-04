FROM jupyter/minimal-notebook:hub-2.1.1

# add in the extensions we need
RUN    conda install -y -c conda-forge jupyter_contrib_nbextensions ; \
       jupyter nbextensions_configurator enable ; \
       jupyter nbextension enable init_cell/main ; \
       jupyter nbextension enable collapsible_headings/main ; \
       jupyter nbextension list

# install the packages needed
WORKDIR /home/jovyan
COPY    --chown=jovyan:users requirements.txt .
RUN     pip install --no-cache-dir -r requirements.txt

USER jovyan
# install the notebooks and trust the notebooks we ship
COPY --chown=jovyan:users notebooks/*.ipynb ./work/
RUN    echo "pwd $PWD" ; \
       echo "ls: $(ls -lAd work/*.ipynb)" ; \
       jupyter trust work/*.ipynb
