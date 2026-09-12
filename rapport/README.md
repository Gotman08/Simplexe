# Coursework report and slides

`rapport.tex` and `presentation.tex` are the original French report and Beamer presentation. The tracked PDFs are coursework deliverables. Their historical timing claims and explanations were not revalidated during the overhaul; current evidence is in [docs/results.md](../docs/results.md).

## Build

The existing Makefile uses `pdflatex` or `latexmk`, French language support and the fonts/packages referenced in the sources. The presentation uses Metropolis. This LaTeX build was not exercised in the new validation.

```bash
cd rapport
make
make slides
make latexmk
make clean
```

The figures referenced by the sources remain under `../Resultats/`, so their paths are preserved. Source attribution is retained. Generated auxiliary files are ignored; PDFs remain versioned as the original submitted artifacts.
