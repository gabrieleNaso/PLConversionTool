def build_project_summary() -> dict:
    return {
        "project": "PLConversionTool",
        "objective": (
            "Convertire sequenziatori PLC AWL in un pacchetto XML importabile in "
            "TIA Portal V20 composto sempre da FB GRAPH, GlobalDB e FC LAD."
        ),
        "targets": [
            "TIA Portal V20",
            "GRAPH V2",
            "SW.Blocks.FB importabile",
            "SW.Blocks.GlobalDB del pacchetto",
            "SW.Blocks.FC LAD del pacchetto",
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
