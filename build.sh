#!/bin/bash
set -e

function clear_build () {
  rm -rf build dist *.egg-info
}

PYVER=$(python -c 'import sys; print(sys.version_info[0])')
if [[ PYVER -ne 3 ]];then
  echo "The script should be run on python3"
  exit 1
fi

if [[ "$1" == "clear" ]]; then
  clear_build
  exit 0
fi

if [[ ("$1" = "test" && "$2" != "--ignore-test") || ("$1" = "build") || ("$1" = "deploy") ]]; then
  pip3 install -r requirements.txt

  VER=$(cat VERSION)
  rm -rf ${VER}
  mkdir -p ${VER}

  MOD_VER=$(curl http://tbears.icon.foundation.s3-website.ap-northeast-2.amazonaws.com/earlgrey/VERSION)
  wget "http://tbears.icon.foundation.s3-website.ap-northeast-2.amazonaws.com/earlgrey/earlgrey-${MOD_VER}-py3-none-any.whl" -P ${VER}
  pip install --force-reinstall "${VER}/earlgrey-${MOD_VER}-py3-none-any.whl"

  MOD_VER=$(curl http://tbears.icon.foundation.s3-website.ap-northeast-2.amazonaws.com/iconcommons/VERSION)
  wget "http://tbears.icon.foundation.s3-website.ap-northeast-2.amazonaws.com/iconcommons/iconcommons-${MOD_VER}-py3-none-any.whl" -P ${VER}
  pip install --force-reinstall "${VER}/iconcommons-${MOD_VER}-py3-none-any.whl"

  if [[ -z "${ICONSERVICEPATH}" || ("$1" = "deploy") ]]; then
    wget "http://tbears.icon.foundation.s3-website.ap-northeast-2.amazonaws.com/${VER}/iconservice-${VER}-py3-none-any.whl" -P ${VER}
    pip install --force-reinstall "${VER}/iconservice-${VER}-py3-none-any.whl"
  else
    if [ "$(pip3 list | grep iconservice)" ]; then
        pip uninstall iconservice -y
    fi
    export PYTHONPATH=${ICONSERVICEPATH}:${PYTHONPATH}
  fi

  if [[ "$2" != "--ignore-test" ]]; then
    # python setup.py test
    python -m unittest
  fi

  if [ "$1" = "build" ] || [ "$1" = "deploy" ]; then
    pip install wheel
    clear_build
    python setup.py bdist_wheel

    if [ "$1" = "deploy" ]; then
      cp dist/*${VER}*.whl ${VER}
      cp docs/tbears_jsonrpc_api_v3.md docs/tbears_tutorial.md ${VER}
      wget "http://tbears.icon.foundation.s3-website.ap-northeast-2.amazonaws.com/${VER}/CHANGELOG.md" -P ${VER}
      wget "http://tbears.icon.foundation.s3-website.ap-northeast-2.amazonaws.com/${VER}/dapp_guide.md" -P ${VER}
      tar -cvzf tbears-${VER}.tar.gz ${VER}/*.whl ${VER}/*.md
      mv tbears-${VER}.tar.gz ${VER}

      if [[ -z "${AWS_ACCESS_KEY_ID}" || -z "${AWS_SECRET_ACCESS_KEY}" ]]; then
        echo "Error: AWS keys should be in your environment"
        rm -rf ${VER}
        exit 1
      fi

      pip install awscli
      aws s3 cp ${VER}/tbears-${VER}.tar.gz s3://tbears.icon.foundation --acl public-read
      aws s3 cp ${VER}/CHANGELOG.md s3://tbears.icon.foundation --acl public-read
    fi
  fi

  rm -rf ${VER}
else
  echo "Usage: build.sh [test|build|deploy]"
  echo "  test: run test"
  echo "  clear: clear build and dist files"
  echo "  build: run test and build"
  echo "  build --ignore-test: run build"
  echo "  deploy: run test, build and deploy to s3"
  echo "  deploy --ignore-test: run build and deploy to s3"
  exit 1
fi

