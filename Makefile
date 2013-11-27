NAME       = softwarecollections
SPEC       = $(NAME).spec
VERSION    = $(shell rpmspec -q --qf '%{version}\n' $(SPEC) | head -n 1)
SOURCE_DIR = $(shell rpm --eval '%_sourcedir')
SOURCE     = $(SOURCE_DIR)/$(NAME)-$(VERSION).tar.gz


.PHONY: rpm
rpm: $(SOURCE)
	rpmbuild -ba $(SPEC)

$(SOURCE): $(SOURCE_DIR)
	git archive --format=tar.gz -o $(SOURCE) --prefix=$(NAME)-$(VERSION)/ HEAD

$(SOURCE_DIR):
	mkdir -p $(SOURCE_DIR)
