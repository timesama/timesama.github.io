all: build

cv.html: cv/Resume_for_Frehers.tex
	(cd cv && git pull && docker run --rm --volume="$${PWD}:$${PWD}" --volume="$${PWD}/..:$${PWD}/.." --workdir "$${PWD}" texlive-tidy:latest make4ht -e ../mybuild.mk4 -uf html5+staticsite+tidy Resume_for_Frehers.tex || true)
	mv cv/*.html cv.html
	mv cv/*.css assets/cv.css
	sed -i assets/cv.css  -e "s,body{margin:4em;},,g"
	sed -i assets/cv.css  -e "s,.centerline {text-align:center;},,g"
	sed -i cv.html -e "s,styles:,layout: page,g"
	sed -i cv.html -e "s,title: '',title: CV,g"
	sed -i cv.html -e 's,_*</p>,</p>,g'
	sed -i cv.html -e "s,[_a-z0-9A-Z-]\+\.css,assets/cv.css,g"

build: cv.html
	docker run --rm \
	  --volume="$${PWD}:/srv/jekyll" \
	  --volume="/var/www/html:/var/www/html" \
	  --volume="$${PWD}/vendor/bundle:/usr/local/bundle" \
	  jekyll/jekyll:3.8 \
	  jekyll build

serve:
	docker run --rm -it \
	  --volume="$${PWD}:/srv/jekyll" \
	  --volume="/var/www/html:/var/www/html" \
	  --volume="$${PWD}/vendor/bundle:/usr/local/bundle" \
	  -p 4000:4000 -p 4001:4001 \
	  jekyll/jekyll:3.8 \
	  jekyll serve --livereload-port 4001 -wl --future

.PHONY: all build serve
