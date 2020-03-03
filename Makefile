all: install

install:
	mkdir -p $(DESTDIR)/usr/share/pardus/pdebi
	@cp -fr main.py $(DESTDIR)/usr/share/pardus/pdebi/main.py
	@cp -fr actions.py $(DESTDIR)/usr/share/pardus/pdebi/actions.py
	@cp -fr main.glade $(DESTDIR)/usr/share/pardus/pdebi/main.glade
	@cp -fr icon.svg $(DESTDIR)/usr/share/pardus/pdebi/icon.svg

	mkdir -p $(DESTDIR)/usr/bin
	@cp -fr pdebi $(DESTDIR)/usr/bin/pdebi
	@cp -fr pdebi-action $(DESTDIR)/usr/bin/pdebi-action

	mkdir -p $(DESTDIR)/usr/share/applications
	@cp -fr pdebi.desktop $(DESTDIR)/usr/share/applications/pdebi.desktop

	mkdir -p $(DESTDIR)/usr/share/locale/tr/LC_MESSAGES
	@msgfmt po/tr.po -o $(DESTDIR)/usr/share/locale/tr/LC_MESSAGES/pdebi.mo

	mkdir -p $(DESTDIR)/usr/share/polkit-1/actions
	@cp -fr pdebi-action.policy $(DESTDIR)/usr/share/polkit-1/actions/pdebi-action.policy

uninstall:
	@rm -fr $(DESTDIR)/usr/share/pardus/pdebi
	@rm -fr $(DESTDIR)/usr/bin/pdebi
	@rm -fr $(DESTDIR)/usr/bin/pdebi-action
	@rm -fr $(DESTDIR)/usr/share/applications/pdebi.desktop
	@rm -fr $(DESTDIR)/usr/share/locale/tr/LC_MESSAGES/pdebi.mo
	@rm -fr $(DESTDIR)/usr/share/polkit-1/actions/pdebi-action.policy

.PHONY: install uninstall

