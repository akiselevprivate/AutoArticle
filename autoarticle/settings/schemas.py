collection_schema = {
    "properties": {
        "collections": {
            "type": "array",
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"},
                        "categories": {"type": "array", "items": {"type": "string"}},
                        "amount": {"type": "integer"},
                    },
                    "required": ["topic", "categories", "amount"],
                },
            },
        }
    },
    "required": ["collections"],
    "type": "object",
}
