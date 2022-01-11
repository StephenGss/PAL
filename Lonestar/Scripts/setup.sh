#!/bin/bash

#node details for log
echo "$SLURM_JOB_NODELIST"
free -mh

#transfer all files
cp tournament_files/HUGA_100game_shared_test.zip /tmp/
unzip /tmp/HUGA_100game_shared_test.zip -d /tmp/tournament/
cp ../agent_drop/bbn-agent.simg /tmp/
cp ../agent_drop/pal-v4.simg /tmp/

cp pal/pal.tar.gz /tmp/
tar xzf /tmp/pal.tar.gz -C /tmp
