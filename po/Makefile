# Makefile cppp-repoutils using GNU gettext.
#

PACKAGE = cppp-repoutils
VERSION = v0.1.0
PACKAGE_BUGREPORT = cpppteam@email.cn
LANGUAGE = python
CHARSET = UTF-8

srcdir = .
top_srcdir = ..
srccode_dir = $(top_srcdir)/src

MSGFMT = msgfmt
XGETTEXT_ = xgettext
MSGMERGE = msgmerge
MSGMERGE_UPDATE = $(MSGMERGE) --update
MSGINIT = msginit
MSGCONV = msgconv
MSGFILTER = msgfilter
MSGCAT = msgcat

PYTHON_EXT = .py
POT_EXT = .pot
PO_EXT = .po
MO_EXT = .mo

$(PACKAGE)$(POT_EXT): $(srccode_dir)/*$(PYTHON_EXT)
	$(XGETTEXT_) --language=$(LANGUAGE) \
		--default-domain=$(PACKAGE) --package-name=$(PACKAGE) --package-version=$(VERSION) \
		--msgid-bugs-address=$(PACKAGE_BUGREPORT) \
		--directory=$(srccode_dir) \
		--output=$@ \
		--keyword=_ \
		--from-code=$(CHARSET) \
		$^

update-po: $(srcdir)/*$(PO_EXT)
	for file in $^; do \
		$(MSGMERGE_UPDATE) --backup=none --no-fuzzy-matching --no-location --no-wrap \
		--width=79 --sort-output \
	    $$file $(PACKAGE)$(POT_EXT); \
	done

all: $(PACKAGE)$(POT_EXT) update-po

NEWFILE_NAME = $(LOCALE)$(PO_EXT)
new: all
	if [ -f $(NEWFILE_NAME) ]; then \
		echo "File '$(NEWFILE_NAME)' already exists."; exit 1; \
	elif [ "$(NEWFILE_NAME)" = "$(PO_EXT)" ]; then \
		echo "You must specify a locale name by LOCALE=<locale-name>."; exit 1; \
	else \
		$(MSGINIT) --input=$(PACKAGE)$(POT_EXT) --output=$(NEWFILE_NAME) --locale=$(LOCALE) \
			--no-wrap --width=79; \
	fi
