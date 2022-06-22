#!/bin/sh

which pyenv &> /dev/null
if [[ $? -eq 0 ]]; then
  echo Pyenv found, setting version to system
  export PYENV_VERSION=system
  pyenv version | grep -q system
  if [[ $? -ne 0 ]]; then
    echo ERROR failed to set pyenv version to system
    exit 1
  fi
fi

pip install pydot configargparse networkx numpy > /dev/null
