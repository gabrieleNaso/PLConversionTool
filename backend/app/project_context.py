def build_project_summary() -> dict:
    return {
        "project": "PLConversionTool",
        "objective": (
            "Convertire sequenziatori PLC AWL in un pacchetto XML importabile in "
            "TIA Portal V20 composto sempre da FB GRAPH, GlobalDB e FC LAD."
        ),
        "architecturalRule": (
            "I blocchi del pacchetto devono restare coerenti tra loro: riferimenti, "
            "member DB, naming, logiche LAD e assunzioni GRAPH non possono divergere "
            "fra FB, GlobalDB, FC LAD o eventuali blocchi aggiuntivi."
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
            {
                "name": "frontend/",
                "purpose": "Interfaccia di supporto per il progetto.",
            },
            {
                "name": "tia_bridge/",
                "purpose": "Boundary service verso il Windows agent e TIA Portal Openness.",
            },
            {
                "name": "src/",
                "purpose": "Core converter deterministico: modello intermedio, profili target e generatori.",
            },
            {
                "name": "data/datasets/typicals/",
                "purpose": "XML di riferimento per reverse engineering.",
            },
            {
                "name": "data/datasets/golden/",
                "purpose": "Campioni validati da usare per regression test.",
            },
            {"name": "data/output/", "purpose": "XML e report generati dal tool."},
        ],
    }
