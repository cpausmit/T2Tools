#!/bin/bash
#---------------------------------------------------------------------------------------------------
# Install the t2tools interface.
#---------------------------------------------------------------------------------------------------
#echo -n ' Name of the proxy account used: '
#read T2TOOLS_TICKET
#if [ -z "$T2TOOLS_TICKET" ]
#then
#   T2TOOLS_TICKET=$USER
#  echo " Set T2TOOLS_TICKE=$T2TOOLS_TICKET"
#fi
#echo -n ' Name of the Tier-2 account used: '
#read T2TOOLS_USER
#if [ -z "$T2TOOLS_USER" ]
#then
#  T2TOOLS_USER=$USER
#  echo " Set T2TOOLS_USER=$T2TOOLS_USER"
#fi

# generate the setup file
rm -f setup.sh
touch setup.sh

# first the base directory and the path
echo "# CAREFUL THIS FILE IS GENERATED AT INSTALL"                  >> setup.sh
#echo "export T2TOOLS_TICKET=\$1"                                    >> setup.sh
#echo "[ -z \"\$T2TOOLS_TICKET\" ] && export T2TOOLS_TICKET=$USER"   >> setup.sh
#echo "export T2TOOLS_USER=\$2"                                      >> setup.sh
#echo "[ -z \"\$T2TOOLS_USER\" ] && export T2TOOLS_USER=$USER"       >> setup.sh
#echo ""                                                             >> setup.sh
echo "export T2TOOLS_DEBUG=0"                                       >> setup.sh
#echo "export T2TOOLS_SERVER=t2bat0380.cmsaf.mit.edu"                >> setup.sh
#echo "export T2TOOLS_SERVER=se01.cmsaf.mit.edu"                     >> setup.sh
#echo "export T2TOOLS_SERVER=t2srv0017.cmsaf.mit.edu"                >> setup.sh
echo "export T2TOOLS_BASE=`pwd`"                                    >> setup.sh
echo "export PATH=\"\${PATH}:\${T2TOOLS_BASE}/bin\""                >> setup.sh
echo "export PYTHONPATH=\"\${PYTHONPATH}:\${T2TOOLS_BASE}/python\"" >> setup.sh

exit 0
