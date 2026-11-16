#!/bin/bash
#---------------------------------------------------------------------------------------------------
# Install the t2tools interface: generate setup.sh for the present location.
#
# Server, user and mount point of the Tier-2 storage are defined in config/t2tools.cfg.
#---------------------------------------------------------------------------------------------------
cd `dirname $0`

cat > setup.sh <<EOS
# CAREFUL THIS FILE IS GENERATED AT INSTALL (install.sh)
# usage: source setup.sh [ <ticket> [ <user> ] ]   (arguments kept for backward compatibility)
export T2TOOLS_TICKET=\$1
[ -z "\$T2TOOLS_TICKET" ] && export T2TOOLS_TICKET=\$USER
export T2TOOLS_USER=\$2
[ -z "\$T2TOOLS_USER" ] && export T2TOOLS_USER=\$USER

export T2TOOLS_DEBUG=0
export T2TOOLS_BASE=`pwd`
export PATH="\${PATH}:\${T2TOOLS_BASE}/bin"
EOS

echo " Generated: `pwd`/setup.sh"
exit 0
