#! /bin/bash

FORCE=0
# parse the options
while getopts ':fh-:' opt ; do
    case $opt in
        -)
            case "${OPTARG}" in
                force)
                    FORCE=1 ;;
            esac;;
        f)
            FORCE=1
            echo "warning: forced installation"
            ;;
        h)
            echo "usage: $0 [-h] [--force]" >&2
            exit 2
            ;;
        *)
            echo "Invalid argument: '-${OPTARG}'" >&2
            echo "usage: $0 [-h] [--force]" >&2
            exit 2
            ;;
    esac
done

if [ -f /home/invenio/reroils/bin/activate ] && [ $FORCE == 0 ]; then
    echo "Already installed!"
    source reroils/bin/activate
else
    # create virtualenv if does not exists
    if [ ! -f /home/invenio/reroils/bin/activate ]; then
        virtualenv reroils
    fi

    # activate virtualenv
    source reroils/bin/activate

    # install nodejs tools done in the image
    # npm install -g --prefix ${VIRTUAL_ENV} npm
    # npm install -g --prefix ${VIRTUAL_ENV} r node-sass clean-css clean-css-cli requirejs uglify-js

    # clone the sources if does not exists
    mkdir -p reroils/src
    cd reroils/src

    if [ ! -f reroils-app ]; then
        git clone https://github.com/rero/reroils-app.git
    fi

    # install the invenio application
    cd reroils-app
    pip install -r requirements-devel.txt
    pip install -e .[all]

    # collect and install js dependencies
    invenio npm
    cd /home/invenio/reroils/var/instance/static
    npm install
    npm install --save angular-schema-form

    # collect static files
    invenio collect -v

    # test the assets
    invenio assets build
    echo "Installation done!"


fi
