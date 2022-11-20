(define (problem craft_pogo_stick)
        (:domain pogo_stick)
        (:objects
                map inv not_created yellow_box
                tree1 tree2 tree3 tree4 
                crafting_table1
		diamond_ore1
		Pt_block1 Pt_block2 Pt_block3
		blue_key1
        )

        (:init
                (MAP map) (INVENTORY inv) (NOT_CREATED not_created) (YELLOW_BOX yellow_box)
                (TREE tree1) (IN tree1 map)
                (TREE tree2) (IN tree2 map)
                (TREE tree3) (IN tree3 map)
                (TREE tree4) (IN tree4 map)
                (CRAFTING_TABLE crafting_table1) (IN crafting_table1 map)
		(DIAMOND_ORE diamond_ore1) (IN diamond_ore1 map)
		(Pt_BLOCK Pt_block1) (IN Pt_block1 map)
		(Pt_BLOCK Pt_block2) (IN Pt_block2 map)
		(Pt_BLOCK Pt_block3) (IN Pt_block3 map)
		(BLUE_KEY blue_key1) (IN blue_key1 yellow_box)

		(= (wood_log-amount inv) 0)
		(= (wood_plank-amount inv) 0)
		(= (stick-amount inv) 0)
		(= (rubber_sac-amount inv) 0)
		(= (pogo_stick-amount inv) 0)
		(= (diamond_shard-amount inv) 0)
		(= (diamond_block-amount inv) 0)
		(= (Pt_block-amount inv) 0)
		(= (Ti_block-amount inv) 0)
		(= (blue_key-amount inv) 0)
        )

        (:goal (> (pogo_stick-amount inv) 0)
        )
)
