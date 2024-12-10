# EasyEdital

## Setup 
To set up the env, you need conda, mamba, micromamba or alike. We provided an environment file for the setup.

```
micromamba env create -f environment.yaml
pip install pymupdf
```

Note: the `pymupdf` package must be installed after `fitz` to prevent dependency problems so we
install it after setting up the environment.

```
micromamba activate easy-edital
```

## Requirements
```
pnpm
```

### Python
```
python=3.12
ipykernel
pandas
nltk
numpy
pytorch
transformers
sentence-transformers
scikit-learn
fastapi
pytesseract
matplotlib
aiofiles
python-docx
beautifulsoup4
pdf2image
striprtf
fuzzywuzzy
fitz
pymupdf
frontend
tools
```

## Credits
- Bernardo Maia Coelho
- Gustavo Wadas Lopes
- Pedro Guilherme dos Reis Teixeira
- Pedro Henrique Vilela do Nascimento
