NAME=writeup
DOC=writeup

all: compile clean
compile: $(DOC).tex
	pdflatex $(DOC).tex
	pdflatex $(DOC).tex
	pdflatex $(DOC).tex
	mv $(DOC).pdf $(NAME).pdf
clean:
	rm *.aux *.log
