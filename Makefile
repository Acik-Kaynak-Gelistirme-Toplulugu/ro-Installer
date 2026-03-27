NAME=ro-installer
VERSION=1.0.0
# COPR'ın SRPM üretiminde çıktıları bıraktığı dizin OUTDIR'dır. COPR default OUTDIR=. yollar.
OUTDIR ?= .

.PHONY: srpm tarball clean

tarball:
	@echo ">>> Kaynak kodlar (tar.gz) arşivleniyor..."
	mkdir -p $(NAME)-$(VERSION)
	rsync -a --exclude='$(NAME)-$(VERSION)' \
	         --exclude='.git' \
	         --exclude='.dart_tool' \
	         --exclude='.pub-cache' \
	         --exclude='build' \
	         --exclude='*.tar.gz' \
	         --exclude='*.rpm' \
	         ./ $(NAME)-$(VERSION)/
	tar -czf $(NAME)-$(VERSION).tar.gz $(NAME)-$(VERSION)
	rm -rf $(NAME)-$(VERSION)

srpm: tarball
	@echo ">>> Geçici rpmbuild ortamı oluşturuluyor ve SRPM derleniyor..."
	mkdir -p rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
	cp ro-installer.spec rpmbuild/SPECS/
	mv $(NAME)-$(VERSION).tar.gz rpmbuild/SOURCES/
	
	rpmbuild -bs --nodeps --define "_topdir $$(pwd)/rpmbuild" rpmbuild/SPECS/ro-installer.spec
	
	@echo ">>> Üretilen .src.rpm dosyasi $(OUTDIR) dizinine aktarılıyor..."
	mkdir -p $(OUTDIR)
	mv rpmbuild/SRPMS/*.src.rpm $(OUTDIR)/
	
	@echo ">>> Geçici ortam temizleniyor..."
	rm -rf rpmbuild

clean:
	rm -rf rpmbuild
	rm -f *.tar.gz
	rm -f *.rpm
