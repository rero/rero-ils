# Configuration
SOURCE=resources.dot
NAME=reroils_resources

# `make graphs` generates all graphs
graphs: ${NAME}.svg ${NAME}.png

# SVG graph
${NAME}.svg: ${SOURCE}
	@dot -Tsvg $< -o $@

# PNG graph
${NAME}.png: ${SOURCE}
	@dot -Tpng $< -o $@

# `make clean` removes all PNG and SVG files
clean:
	@rm -f ${NAME}.svg ${NAME}.png
