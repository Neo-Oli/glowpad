s:

install: s
	sed -e '1s|#!.*/sh|#!$(shell which sh)|' \
		s > $(PREFIX)/bin/s
		chmod +x $(PREFIX)/bin/s
		ln -sf $(PREFIX)/bin/s $(PREFIX)/bin/S

uninstall:
	rm -f $(PREFIX)/bin/s
	rm -f $(PREFIX)/bin/S

.PHONY: install uninstall
