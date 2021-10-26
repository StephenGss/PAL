docker run --rm -e PAL_AGENT_PORT=9000 --network=host --user $(id -u):$(id -g) --workdir=/workdir sri/episodic-curiosity:dryrun 'python3 /build/sri-episodic-curiosity/custom_launcher_script.py --workdir=/workdir --scenario=polycraft:Tournament --stage=target --issue_novelty_action --num_env=1 --nouse_eval_envs --base_seed=42 --method=ppo_plus_eco --polycraft_policy_architecture=hybrid_cnn --polycraft_base_reward=simple --polycraft_shaping=macguffin+proximity --polycraft_forbid_placemacguffin_failure --polycraft_obs_augments=EncodeNonSpatialFeatures --r_network_training_interval=999999999'