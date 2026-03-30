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
            {"name": "src/", "purpose": "Core converter e logiche riusabili."},
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
