(define (domain pogo_stick)
	(:requirements :fluents)
	
	(:functions
		(wood_log-amount ?inv)
		(wood_plank-amount ?inv)
		(stick-amount ?inv)
		(rubber_sac-amount ?inv)
		(pogo_stick-amount ?inv)
		(diamond_shard-amount ?inv)
		(diamond_block-amount ?inv)
		(Pt_block-amount ?inv)
		(Ti_block-amount ?inv)
		(blue_key-amount ?inv)
	)
	
        (:predicates
                (MAP ?x) (INVENTORY ?x) (NOT_CREATED ?x) (YELLOW_BOX ?x)
                (TREE ?x) (CRAFTING_TABLE ?x)
                (IN ?x ?y)
		(DIAMOND_ORE ?x)
		(Pt_BLOCK ?x)
		(BLUE_KEY ?x)
        )
    
        (:action GET_WOOD_BLOCK
                :parameters (?map ?inv ?not_created ?tree)
                :precondition (and
                                (MAP ?map)
                                (INVENTORY ?inv)
                                (NOT_CREATED ?not_created)
                                (TREE ?tree) (IN ?tree ?map)
				)
                :effect (and
				(increase (wood_log-amount ?inv) 1)
				(IN ?tree ?not_created)
                               (not (IN ?tree ?map))
                         )
        )

        (:action CRAFT_WOOD_PLANKS
                :parameters (?inv)
                :precondition (and
                                (INVENTORY ?inv)
				(> (wood_log-amount ?inv) 0)
				)
                :effect (and 
				(increase (wood_plank-amount ?inv) 4)
				(decrease (wood_log-amount ?inv) 1)
			)
        )

        (:action CRAFT_STICKS
                :parameters (?inv)
                :precondition (and
                                (INVENTORY ?inv)
				(> (wood_plank-amount ?inv) 1)
                                )
                :effect (and
				(increase (stick-amount ?inv) 4)
				(decrease (wood_plank-amount ?inv) 2)
			)
        )
	
        (:action CRAFT_TREE_TAP
                :parameters (?map ?inv ?tree ?crafting_table)
                :precondition (and
                                (MAP ?map)
                                (INVENTORY ?inv)
                                (TREE ?tree) (IN ?tree ?map)
                                (CRAFTING_TABLE ?crafting_table) (IN ?crafting_table ?map)
				(> (wood_plank-amount ?inv) 4)
				(> (stick-amount ?inv) 0)
                                )
                :effect (and
				(increase (rubber_sac-amount ?inv) 1)
				(decrease (wood_plank-amount ?inv) 5)
				(decrease (stick-amount ?inv) 1)
			)
        )

        (:action GET_DIAMOND_ORE
                :parameters (?map ?inv ?not_created ?diamond_ore)
                :precondition (and
                                (MAP ?map)
                                (INVENTORY ?inv)
                                (NOT_CREATED ?not_created)
                                (DIAMOND_ORE ?diamond_ORE) (IN ?diamond_ORE ?map)
				)
                :effect (and
				(increase (diamond_shard-amount ?inv) 9)
				(IN ?diamond_ore ?not_created)
                               (not (IN ?diamond_ore ?map))
                         )
        )

        (:action CRAFT_DIAMOND_BLOCK
                :parameters (?map ?inv ?crafting_table)
                :precondition (and
                                (MAP ?map)
                                (INVENTORY ?inv)
                                (CRAFTING_TABLE ?crafting_table) (IN ?crafting_table ?map)
				(> (diamond_shard-amount ?inv) 8)
                                )
                :effect (and
				(increase (diamond_block-amount ?inv) 1)
				(decrease (diamond_shard-amount ?inv) 9)
			)
        )

        (:action GET_Pt_BLOCK
                :parameters (?map ?inv ?not_created ?Pt_block)
                :precondition (and
                                (MAP ?map)
                                (INVENTORY ?inv)
                                (NOT_CREATED ?not_created)
                                (Pt_BLOCK ?Pt_block) (IN ?Pt_block ?map)
				)
                :effect (and
				(increase (Pt_block-amount ?inv) 1)
				(IN ?Pt_block ?not_created)
                                (not (IN ?Pt_block ?map))
                         )
        )

        (:action TRADE_Pt_Ti
                :parameters (?inv)
                :precondition (and
                                (INVENTORY ?inv)
				(> (Pt_block-amount ?inv) 0)
				)
                :effect (and
				(increase (Ti_block-amount ?inv) 1)
				(decrease (Pt_block-amount ?inv) 1)
                         )
        )

        (:action TRADE_WOOD_Ti
                :parameters (?inv)
                :precondition (and
                                (INVENTORY ?inv)
				(> (wood_log-amount ?inv) 9)
				)
                :effect (and
				(increase (Ti_block-amount ?inv) 1)
				(decrease (wood_log-amount ?inv) 10)
                         )
        )

        (:action TRADE_Pt_DIAMOND
                :parameters (?inv)
                :precondition (and
                                (INVENTORY ?inv)
				(> (Pt_block-amount ?inv) 1)
				)
                :effect (and
				(increase (diamond_shard-amount ?inv) 9)
				(decrease (Pt_block-amount ?inv) 2)
                         )
        )

        (:action TRADE_DIAMOND_Pt
                :parameters (?inv)
                :precondition (and
                                (INVENTORY ?inv)
				(> (diamond_shard-amount ?inv) 17)
				)
                :effect (and
				(increase (Pt_block-amount ?inv) 1)
				(decrease (diamond_shard-amount ?inv) 18)
                         )
        )

        (:action GET_BLUE_KEY
                :parameters (?inv ?not_created ?yellow_box ?blue_key)
                :precondition (and
                                (INVENTORY ?inv)
                                (NOT_CREATED ?not_created)
                                (YELLOW_BOX ?yellow_box)
                                (BLUE_KEY ?blue_key) (IN ?blue_key ?yellow_box)
				)
                :effect (and
				(increase (blue_key-amount ?inv) 1)
				(IN ?blue_key ?not_created)
                               (not (IN ?blue_key ?yellow_box))
                         )
        )

        (:action PILLAGE_SAFE
                :parameters (?map ?inv ?not_created )
                :precondition (and
                                (INVENTORY ?inv)
                                (> (blue_key-amount ?inv) 0)
				)
                :effect (and
				(increase (diamond_shard-amount ?inv) 18)
				(decrease (blue_key-amount ?inv) 1)
                         )
        )

        (:action CRAFT_POGO_STICK
                :parameters (?map ?inv ?crafting_table)
                :precondition (and
                                (MAP ?map)
                                (INVENTORY ?inv)
                                (CRAFTING_TABLE ?crafting_table) (IN ?crafting_table ?map)
				(> (stick-amount ?inv) 1)
				(> (diamond_block-amount ?inv) 1)
				(> (Ti_block-amount ?inv) 1)
				(> (rubber_sac-amount ?inv) 0)
                                )
                :effect (and
				(increase (pogo_stick-amount ?inv) 1)
				(decrease (stick-amount ?inv) 2)
				(decrease (diamond_block-amount ?inv) 2)
				(decrease (Ti_block-amount ?inv) 2)
				(decrease (rubber_sac-amount ?inv) 1)
			)
        )

)
