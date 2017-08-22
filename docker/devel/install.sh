#! /bin/bash

if [ -f /home/invenio/reroils/bin/activate ]; then
    echo "Already installed!"
    source reroils/bin/activate
else
    # create virtualenv
    virtualenv reroils

    # activate virtualenv
    source reroils/bin/activate

    # install nodejs tools
    npm install -g --prefix ${VIRTUAL_ENV} npm
    npm install -g --prefix ${VIRTUAL_ENV} node-sass clean-css clean-css-cli requirejs uglify-js

    # clone the sources
    mkdir -p reroils/src
    cd reroils/src
    git clone https://github.com/rero/reroils-app.git

    # install the invenio application
    cd reroils-app
    pip install -r requirements-devel.txt
    pip install -e .

    # collect and install js dependencies
    invenio npm
    cd /home/invenio/reroils/var/instance/static
    npm install

    # collect static files
    invenio collect -v

    # test the assets
    invenio assets build
    echo "Installation done!"
fi

