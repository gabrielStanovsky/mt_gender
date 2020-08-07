#!/bin/sh
# ./install.sh
## Install required python packages and downloads resrouces

# install packages
pip install -r ./requirements.txt

# download spacy language support∫
python -m spacy download en
python -m spacy download de
python -m spacy download it
python -m spacy download es
python -m spacy download fr

# Czech morphology annotation
curl --remote-name-all https://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11234/1-1836{/czech-morfflex-pdt-161115.zip}
unzip czech-morfflex-pdt-161115.zip
