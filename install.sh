#!/bin/bash
#---------------------------------------------------------------------------------------------------
# Install the t2tools interface.
#---------------------------------------------------------------------------------------------------
echo -n ' Name of the proxy account used: '
read TICKET_HOLDER
if [ -z "$TICKET_HOLDER" ]
then
  TICKET_HOLDER=$USER
  echo " Set TICKET_HOLDER=$TICKET_HOLDER"
fi
echo -n ' Name of the Tier-2 account used: '
read TIER2_USER
if [ -z "$TIER2_USER" ]
then
  TIER2_USER=$USER
  echo " Set TIER2_USER=$TIER2_USER"
fi

# generate the setup file
rm -f setup.sh
touch setup.sh

# first the base directory and the path
echo "# CAREFUL THIS FILE IS GENERATED AT INSTALL"                  >> setup.sh
echo "export T2TOOLS_DEBUG=0"                                       >> setup.sh
#echo "export T2TOOLS_SERVER=t2bat0380.cmsaf.mit.edu"                >> setup.sh
#echo "export T2TOOLS_SERVER=se01.cmsaf.mit.edu"                     >> setup.sh
echo "export T2TOOLS_SERVER=t2srv0017.cmsaf.mit.edu"                >> setup.sh
echo "export T2TOOLS_TICKET=$TICKET_HOLDER"                         >> setup.sh
echo "export T2TOOLS_USER=$TIER2_USER"                              >> setup.sh
echo "export T2TOOLS_BASE=`pwd`"                                    >> setup.sh
echo "export PATH=\"\${PATH}:\${T2TOOLS_BASE}/bin\""                >> setup.sh
echo "export PYTHONPATH=\"\${PYTHONPATH}:\${T2TOOLS_BASE}/python\"" >> setup.sh
echo ""                                                             >> setup.sh
echo "# reduce memory used on hdfs commands"                        >> setup.sh
echo "export HADOOP_CLIENT_OPTS=-Xmx32m"                            >> setup.sh

exit 0
