slides:
	uv run quarto render . --output-dir docs/slides

preview:
	uv run quarto preview .

clean:
	rm -rf docs/slides/*
