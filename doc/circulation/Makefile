LOANS=loan_states

circulation: ${LOANS}

${LOANS}: ${LOANS}.svg ${LOANS}.png

${LOANS}.svg: ${LOANS}.dot
	@echo "Génération de $@"
	@dot -Tsvg $< -o $@

${LOANS}.png: ${LOANS}.dot
	@echo "Génération de $@"
	@dot -Tpng $< -o $@

clean:
	@echo "Suppression de ${LOANS}.[svg|png]"
	@rm -f ${LOANS}.svg ${LOANS}.png
