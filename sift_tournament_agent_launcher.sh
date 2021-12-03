#!/bin/bash
# Adapted from SIFT tournament_wrapper -sets ENV-vars for OpenMind - DN
# i'm only making this b/c it is faster than trying to recode all the
# env var default stuff in python
DEBUG=1

PROGNAME=$(basename "$0")
warn()  { echo "$PROGNAME: ${@}" 1>&2; }
die()   { warn "${@}"; exit 1; }
dbug()   { test -z $DEBUG || warn "${@}"; }

# example usage:
   #dbug This only prints if DEBUG is defined
   #test -e foo || die file foo must exist
   #test -z $FOO && die Environment variable FOO must be defined

# bash-ism to get location of script.  Must use /bin/pwd to get absolute path.
thisdir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd -P "$( dirname "$SOURCE" )" && /bin/pwd )"
dbug thisdir is $thisdir

export OPENMIND_HOME=${OPENMIND_HOME:-${thisdir}/../..}    # Note this must be an absolute path, docker insists for mounts; hence /bin/pwd above
dbug OPENMIND_HOME is $OPENMIND_HOME

# this stuff and its use farther down is to let inside-docker access X server, per
# https://stackoverflow.com/questions/48235040/run-x-application-in-a-docker-container-reliably-on-a-server-connected-via-ssh-w
# Note the --net host is part of this solution.
# Jenkins doesn't have xauth, so he shouldn't do this stuff.
if [ "$USER" == "jenkins" ]; then
  XAUTH=/tmp    # so the -v mount below just redoes /tmp mount and is happy
else
  XAUTH=/tmp/.$USER-docker.xauth-n
  xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | xauth -f $XAUTH nmerge -
  chmod 777 $XAUTH
fi

export CIRCA_BASEPORT=${CIRCA_BASEPORT:-10000}
dbug CIRCA_BASEPORT is $CIRCA_BASEPORT

export POSS_OPRS_MP_PORT=$(($CIRCA_BASEPORT+5))
dbug POSS_OPRS_MP_PORT is $POSS_OPRS_MP_PORT

export OPRS_MP_PORT=${OPRS_MP_PORT:-${POSS_OPRS_MP_PORT}}
dbug OPRS_MP_PORT is $OPRS_MP_PORT

#export POSS_Polycraft_Port=$(($CIRCA_BASEPORT+7))
export POSS_Polycraft_Port=9000
dbug POSS_Polycraft_Port is $POSS_Polycraft_Port

#export Polycraft_Port=${Polycraft_Port:-${POSS_Polycraft_Port}}
#export Polycraft_Port=${Polycraft_Port:-9000} #Hard Code for now.
export Polycraft_Port=9000  #Hard Code for now.
dbug Polycraft_Port is $Polycraft_Port
export PAL_AGENT_PORT=$Polycraft_Port

export PAL_TM_PORT=$(($CIRCA_BASEPORT+9))
#“PAL_TM_PORT” This is the port our tournament manager uses. (default 9005)
#“PAL_AGENT_PORT” This is the port your agent will use to connect to Polycraft. (default 9000)

#python3 "$@"
#DEBUG=1; ./${OPENMIND_HOME}/prt/prt -vD openmind-polycraft-agent-start-script.prt
exec 4>&2;
exec 3>&1;
# Phase 1 run command
#/usr/bin/env perl ${OPENMIND_HOME}/code/prt/prt --resultsdir "$1"  openmind-in-polycraft-tournament.prt 1>&3 2>&4
# Phase 2 command (24M)
/usr/bin/env perl ${OPENMIND_HOME}/code/prt/prt --resultsdir "$1"  openmind-in-polycraft-v2-domains-tournament.prt 1>&3 2>&4