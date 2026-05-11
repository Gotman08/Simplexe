# Makefile pour compiler le rapport LaTeX
# Usage :
#   make            -> compile rapport.pdf
#   make view       -> compile et ouvre le PDF
#   make clean      -> supprime les fichiers auxiliaires (.aux, .log, .out, .toc)
#   make mrproper   -> nettoyage total + supprime le PDF

LATEX   ?= pdflatex
LATEXMK ?= latexmk
DOC     := rapport
PDF     := $(DOC).pdf
TEX     := $(DOC).tex
SLIDES_DOC := presentation
SLIDES_PDF := $(SLIDES_DOC).pdf
SLIDES_TEX := $(SLIDES_DOC).tex
SLIDES_NAV := $(SLIDES_DOC).nav $(SLIDES_DOC).snm $(SLIDES_DOC).vrb

AUX_FILES := *.aux *.log *.out *.toc *.lof *.lot *.fls *.fdb_latexmk *.synctex.gz $(SLIDES_NAV)

.PHONY: all view slides slides-view clean mrproper help latexmk

all: $(PDF) $(SLIDES_PDF)

$(PDF): $(TEX)
	@echo "==> Compilation LaTeX du rapport (3 passes)"
	$(LATEX) -interaction=nonstopmode $(TEX) > /dev/null
	$(LATEX) -interaction=nonstopmode $(TEX) > /dev/null
	$(LATEX) -interaction=nonstopmode $(TEX)
	@echo "==> $(PDF) genere"

slides: $(SLIDES_PDF)

$(SLIDES_PDF): $(SLIDES_TEX)
	@echo "==> Compilation Beamer de la presentation (2 passes)"
	$(LATEX) -interaction=nonstopmode $(SLIDES_TEX) > /dev/null
	$(LATEX) -interaction=nonstopmode $(SLIDES_TEX)
	@echo "==> $(SLIDES_PDF) genere"

latexmk:
	$(LATEXMK) -pdf -interaction=nonstopmode $(TEX)
	$(LATEXMK) -pdf -interaction=nonstopmode $(SLIDES_TEX)

view: $(PDF)
	@$(MAKE) -s _open FILE=$(PDF)

slides-view: $(SLIDES_PDF)
	@$(MAKE) -s _open FILE=$(SLIDES_PDF)

_open:
	@if command -v xdg-open > /dev/null; then xdg-open $(FILE) & \
	elif command -v open > /dev/null;     then open $(FILE) & \
	else echo "Ouvrir manuellement : $(FILE)"; fi

clean:
	@rm -f $(AUX_FILES)
	@echo "==> Fichiers auxiliaires supprimes"

mrproper: clean
	@rm -f $(PDF) $(SLIDES_PDF)
	@echo "==> $(PDF) et $(SLIDES_PDF) supprimes"

help:
	@echo "Cibles disponibles :"
	@echo "  make             -> compile rapport.pdf ET presentation.pdf"
	@echo "  make $(DOC)      -> rapport seul"
	@echo "  make slides      -> presentation Beamer seule"
	@echo "  make view        -> compile et ouvre le rapport"
	@echo "  make slides-view -> compile et ouvre la presentation"
	@echo "  make latexmk     -> alternative via latexmk"
	@echo "  make clean       -> nettoie les .aux/.log/.toc/..."
	@echo "  make mrproper    -> clean + supprime les PDF"
