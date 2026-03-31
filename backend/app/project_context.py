def build_project_summary() -> dict:
    return {
        "project": "PLConversionTool",
        "objective": (
            "Convertire sequenziatori PLC AWL in blocchi GRAPH XML importabili in "
            "TIA Portal V20, con GlobalDB companion separato e supporto FC LAD."
        ),
        "targets": [
            "TIA Portal V20",
            "GRAPH V2",
            "SW.Blocks.FB importabile",
            "SW.Blocks.GlobalDB companion",
            "SW.Blocks.FC LAD di supporto",
        ],
        "repositoryAreas": [
            {"name": "backend/", "purpose": "API e orchestrazione del workflow."},
            {"name": "frontend/", "purpose": "Interfaccia di supporto per il progetto."},
            {
                "name": "tia_bridge/",
                "purpose": "Boundary service verso il Windows agent e TIA Portal Openness.",
            },
            {
                "name": "src/",
                "purpose": "Core converter deterministico: modello intermedio, profili target e generatori.",
            },
            {
                "name": "datasets/typicals/",
                "purpose": "XML di riferimento per reverse engineering.",
            },
            {
                "name": "datasets/golden/",
                "purpose": "Campioni validati da usare per regression test.",
            },
            {"name": "output/", "purpose": "XML e report generati dal tool."},
        ],
    }
