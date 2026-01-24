# Makefile for GLAS documentation
# Compiles LaTeX and copies PDF to main folder

TEX = glas_manual.tex
PDF = glas_manual.pdf
BUILD = build

.PHONY: all clean view

all: $(PDF)

$(PDF): $(TEX)
	@mkdir -p $(BUILD)
	latexmk -pdf -output-directory=$(BUILD) $(TEX)
	cp $(BUILD)/$(PDF) .
	@echo "PDF generated: $(PDF)"

clean:
	rm -rf $(BUILD)
	rm -f $(PDF)

view: $(PDF)
	open $(PDF)
